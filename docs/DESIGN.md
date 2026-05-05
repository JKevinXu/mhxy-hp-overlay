# Design: MHXY Visible HP Overlay

## 背景

用户在 macOS 上通过 MuMu 模拟器运行《梦幻西游手游》。目标是建立一个实时血量显示工具，但实现必须限制在屏幕可见信息分析，不接触客户端内部状态。

## Goals

- 从截图/屏幕 ROI 中识别可见血条比例。
- 支持多个命名 ROI，适配我方/队友/目标/怪物等画面区域。
- 在终端或独立 UI 中显示估计血量。
- 本地运行，不上传游戏画面。
- 所有输出标记为可见估计值或可见文本值。

## Non-goals

- 不读内存。
- 不抓包或解析协议。
- 不 hook 图形接口或游戏进程。
- 不修改客户端/模拟器。
- 不自动点击、战斗、走位或任务。
- 不显示画面中不可见的真实血量。

## Architecture

```text
Authorized screen / image file
        |
        v
CaptureSource
  - ImageFileSource
  - MssScreenSource
        |
        v
ROI cropper
        |
        v
HP analyzer
  - red bar HSV detector
  - optional visible text parser
        |
        v
Result model
  - name
  - hp_ratio
  - visible_text
  - confidence
  - evidence/debug metadata
        |
        v
Display
  - JSON
  - terminal table
  - future overlay window
```

## Data model

```python
HPDetection(
    name='target',
    hp_ratio=0.73,
    confidence=0.88,
    visible_text=None,
    source='screen',
    roi=(100, 100, 300, 120),
    method='visible_red_bar_hsv',
)
```

## Detection logic

MVP 使用 HSV 红色阈值：

- red hue low: 0-12
- red hue high: 170-180
- saturation/value 下限过滤暗背景
- 在 ROI 中寻找红色像素按列的覆盖范围
- `hp_ratio = red_columns / possible_bar_columns`

置信度考虑：

- 红色像素数量是否足够。
- 红色列是否连续。
- ROI 是否太小或无效。

## UI 原则

- 不显示 “真实 HP”，显示 “visible estimate”。
- 低置信度结果要淡化或标记 warning。
- 支持手动暂停和退出。
- 默认不保存截图；debug 模式才保存本地图片。

## Compliance checklist for future PRs

每个后续改动必须回答：

- 是否只使用授权屏幕/图片/录屏作为输入？必须是。
- 是否没有内存、封包、hook、注入、客户端修改？必须是。
- 是否没有自动点击/自动输入/自动战斗/自动任务？必须是。
- 如果运行在 Android 模拟器，是否没有 ADB 输入、进程注入、窗口 hook、内存/封包访问？必须是。
- UI 是否标注输出是可见估计值？必须是。
