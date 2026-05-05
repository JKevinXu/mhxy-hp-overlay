# 梦幻西游手游可见血量显示工具 / MHXY Visible HP Overlay

一个面向 macOS + MuMu 模拟器的本地优先视觉工具，用屏幕截图读取游戏画面中“已经可见”的血条/血量文本，并在终端或后续 overlay UI 中显示估计血量状态。

## Important Boundaries / 重要边界

本项目只做可见画面分析：

- 不读取或写入游戏/模拟器内存。
- 不解析网络包、协议或私有日志。
- 不注入、不 hook、不修改客户端或模拟器。
- 不绕过反作弊或系统权限。
- 不执行自动点击、自动战斗、自动任务、ADB 输入或脚本化操作。
- 不显示隐藏状态；所有输出都必须来自用户授权截图/录屏/屏幕画面中肉眼可见的信息。
- “血量”输出默认标记为 estimate/visible，除非画面中明确显示数值文本。

如果后续要接入实时画面，只能使用 macOS 屏幕录制权限下的窗口/区域截图，不接触游戏进程内部状态。

## MVP 能做什么

当前 MVP 提供：

1. 从静态图片或屏幕 ROI 中识别红色血条比例。
2. 可选解析画面中可见的 `当前/最大` 血量文本，例如 `1234/5678`。
3. 以 JSON 或 Rich 表格输出检测结果。
4. 提供合成测试图，验证血条比例识别逻辑。

## 从 GameAutomation 复用的安全经验

参考仓库：/Users/kx/ws/GameAutomation

可复用：

- macOS/MuMu 场景下的屏幕截图思路。
- Retina 逻辑坐标与物理像素缩放处理。
- OpenCV 模板/颜色检测、debug 图输出目录结构。
- 本地配置化 ROI 的模式。

不复用：

- pyautogui click 执行器。
- LaunchAgent 定时自动任务。
- 师门任务 action plan。
- ADB、自动输入、自动游戏流程相关内容。

## 安装

```bash
cd /Users/kx/ws/mhxy-hp-overlay
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## 使用

从图片检测：

```bash
mhxy-hp analyze-image tests/fixtures/synthetic_hp_bar.png --roi 10,10,210,30
```

JSON 输出：

```bash
mhxy-hp analyze-image tests/fixtures/synthetic_hp_bar.png --roi 10,10,210,30 --json
```

实时屏幕采样实验模式：

```bash
mhxy-hp watch-screen --roi 100,100,300,120 --interval 0.5
```

注意：`watch-screen` 只截取屏幕像素，不控制游戏。首次运行可能需要给 Terminal/Python 屏幕录制权限。

## ROI 格式

ROI 使用 `x1,y1,x2,y2`，单位默认为屏幕物理像素。后续可以增加校准工具，把 MuMu 窗口内逻辑坐标转换成屏幕物理坐标。

## 输出含义

- `hp_ratio`: 从红色血条可见长度估算的比例，0.0-1.0。
- `confidence`: 检测置信度，主要基于红色像素数量和连续性。
- `visible_text`: 当前 OCR/正则能看到的文本。MVP 默认不依赖 OCR 引擎。
- `source`: `image` 或 `screen`。

## 后续计划

详见 `docs/plans/2026-05-05-mvp-plan.md`。
