#!/usr/bin/env bash
#
# ccmtc-guides（官網共用靜態說明站容器）一鍵部署
# 流程：本機建置與驗證 → rsync 同步 → 重啟 guides 容器 → 線上路由驗證
#
# 1. 容器定義在 NAS 上 ccmtc-official 的 docker-compose.yml（服務名 guides，見 README「首次部署」）
# 2. 路徑對應與通行碼由 ccmtc-portal 的 src/config/sites.mjs 決定；
#    新增站台時 portal 也要重新部署（rewrite 是建置時產生的）
# 3. 走 SSH 金鑰與限定指令 sudo NOPASSWD，不需輸入密碼
# 4. 需要通行碼的站，通行碼由使用者親自寫在 NAS 的 ccmtc-official/.env
#
# 用法：./deploy_nas.sh              建置並部署全部站
#       ./deploy_nas.sh --no-build   不重新匯入原始檔，直接部署現有 site/

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

REMOTE_USER="kevinkid"
# 預設走 Tailscale（公網 22 埠已關閉）。在家可改走內網：export NAS_HOST=<內網 IP>
REMOTE_HOST="${NAS_HOST:-100.96.102.35}"
HOST="${REMOTE_USER}@${REMOTE_HOST}"
SSH_OPTS=(-o StrictHostKeyChecking=no -o ConnectTimeout=20)
DOCKER_BIN="/var/packages/ContainerManager/target/usr/bin"
REMOTE_DIR="/volume1/docker/ccmtc-guides"
COMPOSE_DIR="/volume1/docker/ccmtc-official"
BASE_URL="https://ccmtc.mooo.com"
# 需要通行碼的站（與 sites.mjs 的 auth 一致；目前 guides 內的站都公開）
LOCKED_SITES="${LOCKED_SITES:-}"

echo "=== 步驟 1：連線檢查 ==="
if ! ssh "${SSH_OPTS[@]}" -o BatchMode=yes "${HOST}" true 2>/dev/null; then
    echo "❌ 金鑰登入失敗（${HOST}）。請確認 Tailscale 已連線，或 export NAS_HOST=<內網 IP>"
    exit 1
fi
echo "✅ 金鑰登入正常"

echo
echo "=== 步驟 2：確認 compose 已有 guides 服務 ==="
if ! ssh "${SSH_OPTS[@]}" -o BatchMode=yes "${HOST}" \
     "grep -qE '^  guides:' '${COMPOSE_DIR}/docker-compose.yml'"; then
    echo "❌ ${COMPOSE_DIR}/docker-compose.yml 還沒有 guides 服務，請先照 README「首次部署」加入。"
    exit 1
fi
echo "✅ guides 服務已定義"

echo
echo "=== 步驟 3：本機建置、驗證與同步 ==="
if [[ "${1:-}" != "--no-build" ]]; then
    python3 "${SCRIPT_DIR}/build/build_site.py"
fi
python3 "${SCRIPT_DIR}/build/verify_site.py" --quick

ssh "${SSH_OPTS[@]}" "${HOST}" "mkdir -p '${REMOTE_DIR}'"
rsync -az --delete --stats \
      -e "ssh ${SSH_OPTS[*]}" \
      --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r \
      --exclude '.*' \
      ./site/ "${HOST}:${REMOTE_DIR}/site/"
rsync -az --inplace -e "ssh ${SSH_OPTS[*]}" --chmod=Fu=rw,Fgo=r ./nginx.conf "${HOST}:${REMOTE_DIR}/nginx.conf"
ssh "${SSH_OPTS[@]}" "${HOST}" "chmod -R a+rX '${REMOTE_DIR}'"
echo "✅ 靜態檔案同步完成"

echo
echo "=== 步驟 4：重啟 guides 容器 ==="
# 輸出寫入臨時日誌檔再判斷退出碼，避免 pipe 吃掉錯誤碼（規範 05 鐵則）
ssh "${SSH_OPTS[@]}" "${HOST}" "
set -e
cd '${COMPOSE_DIR}'
LOG=/tmp/guides-compose.log
sudo ${DOCKER_BIN}/docker-compose up -d guides > \"\$LOG\" 2>&1 || {
  echo '❌ docker-compose 失敗，最後 30 行：'; tail -30 \"\$LOG\"; rm -f \"\$LOG\"; exit 1; }
tail -10 \"\$LOG\"; rm -f \"\$LOG\"
sudo ${DOCKER_BIN}/docker exec ccmtc-guides nginx -t
sudo ${DOCKER_BIN}/docker exec ccmtc-guides nginx -s reload
" < /dev/null
echo "✅ 容器啟動成功且 nginx 設定測試通過"

echo
echo "=== 步驟 5：線上路由驗證 ==="
python3 "${SCRIPT_DIR}/build/verify_site.py" --url "${BASE_URL}" --locked "${LOCKED_SITES}"
