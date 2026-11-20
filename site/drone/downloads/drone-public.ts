// 屏東無人機競賽 程控無人機公版程式（Gigo Drone）
// 擴展網址：https://github.com/gigotoys/GigoDrone
//
// 路線：出發區 → A → B → C → 終點區，每段 200 cm，每段結束都降落
//   第1段穿過穿環一（圓心 70 cm）、第4段穿過穿環二（圓心 50 cm）
// 操作：A 從起飛位置一段一段飛
//       B 刷分：從出發區穿過穿環一，直接降落在 C
//       摸 logo 選起飛位置（S/A/B/C）、長按 logo 看電壓（飛行中無效）
//       A+B 緊急降落；往前飛太久沒到位會自動降落（逾時降落）

let 左右修正 = 0

// ---------- 可調整參數 ----------
// 各段飛行高度（cm），刷分時用第1段高度
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
// 按 A 時飛到哪裡結束：1=A、2=B、3=C、4=終點區
let 結束位置 = 4
// 動作之間的停頓（毫秒）
let 穩定等待時間 = 800
// 往前飛超過幾秒沒到位就原地降落，0 = 不使用
// 按 A 每段用「逾時降落秒數」，按 B 刷分用「刷分逾時降落秒數」
let 逾時降落秒數 = 8
let 刷分逾時降落秒數 = 20

// ---------- 程式狀態（不用改） ----------
let 起飛位置 = 0
let 飛行中 = false
let 緊急停止 = false
let 計時中 = false
let 動作開始時間 = 0
let 本次逾時秒數 = 0

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

// 往前飛，含距離校正與左右修正；限時秒數給逾時降落用
function 往前飛 (飛行距離: number, 限時秒數: number) {
    if (!(緊急停止)) {
        本次逾時秒數 = 限時秒數
        動作開始時間 = input.runningTime()
        計時中 = true
        drone.moveAction(drone.DirectionOptions.Forward, Math.round(飛行距離 * 距離校正 / 100))
        計時中 = false
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

// 升降到指定高度，停一下讓機身穩定
function 升降到 (目標高度: number) {
    drone.setDroneHeight(目標高度)
    basic.pause(穩定等待時間)
}

// 飛一段：起飛 → 調高度 → 往前 → 降落
function 飛一段 (第幾段: number) {
    drone.takeOffAction()
    basic.pause(穩定等待時間)
    if (!(緊急停止)) {
        升降到(段高度(第幾段))
    }
    往前飛(每段距離, 逾時降落秒數)
    drone.landingAction()
    顯示位置(第幾段)
}

// 從起飛位置一段一段飛到結束位置
function 執行任務 () {
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

// 刷分：出發區起飛 → 第1段高度穿過穿環一 → 一次飛 3 段距離 → 降落在 C
function 刷分 () {
    drone.takeOffAction()
    basic.pause(穩定等待時間)
    if (!(緊急停止)) {
        升降到(第1段高度)
    }
    往前飛(每段距離 * 3, 刷分逾時降落秒數)
    drone.landingAction()
    if (緊急停止) {
        basic.showIcon(IconNames.No)
    } else {
        顯示位置(3)
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
        飛行中 = true
        緊急停止 = false
        刷分()
        飛行中 = false
    }
})

input.onButtonPressed(Button.AB, function () {
    緊急停止 = true
    計時中 = false
    drone.landingAction()
    basic.showIcon(IconNames.No)
})

// 摸 logo 選起飛位置（飛行中無效）
input.onLogoEvent(TouchButtonEvent.Pressed, function () {
    if (!(飛行中)) {
        起飛位置 = 起飛位置 + 1
        if (起飛位置 > 3) {
            起飛位置 = 0
        }
        顯示位置(起飛位置)
    }
})

// 長按 logo 看電壓；飛行中不讀，以免搶走無人機的回覆
input.onLogoEvent(TouchButtonEvent.LongPressed, function () {
    if (!(飛行中)) {
        basic.showNumber(drone.droneVoltage())
        顯示位置(起飛位置)
    }
})

// 逾時降落：往前飛太久沒到位（例如被風吹得一直無法停穩），就在原地降落
basic.forever(function () {
    if (計時中 && 本次逾時秒數 > 0) {
        if (input.runningTime() - 動作開始時間 > 本次逾時秒數 * 1000) {
            計時中 = false
            緊急停止 = true
            drone.landingAction()
            basic.showIcon(IconNames.No)
        }
    }
    basic.pause(200)
})

顯示位置(起飛位置)
