// 屏東無人機競賽 程控無人機公版程式（Gigo Drone）
// 擴展網址：https://github.com/gigotoys/GigoDrone
//
// 路線：出發區 → A → B → C → 終點區，每段 200 cm，每段結束都降落
//   第1段穿過穿環一（圓心 70 cm）、第4段穿過穿環二（圓心 50 cm）
// 操作：B 選起飛位置（S/A/B/C）、A 開始、A+B 緊急降落、摸 logo 看電壓

let 左右修正 = 0

// ---------- 可調整參數 ----------
// 各段飛行高度（cm）
let 第1段高度 = 70
let 第2段高度 = 60
let 第3段高度 = 60
let 第4段高度 = 50
// 每段前進距離（cm）
let 每段距離 = 200
// 距離校正（%）：飛不夠遠調大，太遠調小
let 距離校正 = 100
// 左右修正（cm）：正數往右、負數往左
左右修正 = 0
// 降落後停多久再起飛（毫秒）
let 降落後等待時間 = 2000
// 飛到哪裡結束：1=A、2=B、3=C、4=終點區
let 結束位置 = 4
// 高度到位的容許誤差（cm）
let 高度誤差 = 8
// 確認高度最多讀幾次
let 高度確認次數 = 10
// 動作之間的停頓（毫秒）
let 穩定等待時間 = 800
// 低於這個電壓不起飛（V）
let 最低電壓 = 3.6

// ---------- 程式狀態（不用改） ----------
let 起飛位置 = 0
let 飛行中 = false
let 緊急停止 = false

// LED 顯示位置：S、A、B、C、E（終點）
function 顯示位置 (位置: number) {
    if (位置 == 0) {
        basic.showString("S")
    } else if (位置 == 1) {
        basic.showString("A")
    } else if (位置 == 2) {
        basic.showString("B")
    } else if (位置 == 3) {
        basic.showString("C")
    } else {
        basic.showString("E")
    }
}

// 回傳第幾段的飛行高度
function 段高度 (第幾段: number) {
    if (第幾段 == 1) {
        return 第1段高度
    } else if (第幾段 == 2) {
        return 第2段高度
    } else if (第幾段 == 3) {
        return 第3段高度
    } else {
        return 第4段高度
    }
}

// 往前飛，含距離校正與左右修正
function 往前飛 (飛行距離: number) {
    if (!(緊急停止)) {
        drone.moveAction(drone.DirectionOptions.Forward, Math.round(飛行距離 * 距離校正 / 100))
        basic.pause(穩定等待時間)
    }
    if (左右修正 > 0 && !(緊急停止)) {
        drone.moveAction(drone.DirectionOptions.Right, 左右修正)
        basic.pause(穩定等待時間)
    } else if (左右修正 < 0 && !(緊急停止)) {
        drone.moveAction(drone.DirectionOptions.Left, 0 - 左右修正)
        basic.pause(穩定等待時間)
    }
}

// 升降到指定高度，讀高度感測器確認到位
function 升降到 (目標高度: number) {
    drone.setDroneHeight(目標高度)
    let 次數 = 0
    let 目前高度 = drone.droneHeight()
    while (Math.abs(目前高度 - 目標高度) > 高度誤差 && 次數 < 高度確認次數 && !(緊急停止)) {
        basic.pause(穩定等待時間)
        目前高度 = drone.droneHeight()
        次數 = 次數 + 1
    }
    basic.pause(穩定等待時間)
}

// 飛一段：起飛 → 調高度 → 往前 → 降落
function 飛一段 (第幾段: number) {
    drone.takeOffAction()
    basic.pause(穩定等待時間)
    if (!(緊急停止)) {
        升降到(段高度(第幾段))
    }
    往前飛(每段距離)
    drone.landingAction()
    顯示位置(第幾段)
    basic.pause(降落後等待時間)
}

// 從起飛位置一段一段飛到結束位置
function 執行任務 () {
    // 檢查電壓
    let 電壓 = drone.droneVoltage()
    if (電壓 < 最低電壓) {
        basic.showIcon(IconNames.Sad)
        basic.showNumber(電壓)
        緊急停止 = true
    }
    // 依序飛每一段
    let 第幾段 = 起飛位置 + 1
    while (第幾段 <= 結束位置 && !(緊急停止)) {
        飛一段(第幾段)
        第幾段 = 第幾段 + 1
    }
    if (緊急停止) {
        basic.showIcon(IconNames.No)
    } else {
        basic.showIcon(IconNames.Yes)
    }
}

input.onButtonPressed(Button.A, function () {
    if (!(飛行中)) {
        飛行中 = true
        緊急停止 = false
        執行任務()
        飛行中 = false
    }
})

input.onButtonPressed(Button.B, function () {
    if (!(飛行中)) {
        起飛位置 = 起飛位置 + 1
        if (起飛位置 > 3) {
            起飛位置 = 0
        }
        顯示位置(起飛位置)
    }
})

input.onButtonPressed(Button.AB, function () {
    緊急停止 = true
    drone.landingAction()
    basic.showIcon(IconNames.No)
})

input.onLogoEvent(TouchButtonEvent.Pressed, function () {
    basic.showNumber(drone.droneVoltage())
    顯示位置(起飛位置)
})

顯示位置(起飛位置)
