# Changelog

## Unreleased

### Added

- 初始化项目结构。
- 增加批量图片 OCR 的 GUI 与命令行入口。
- 增加 Markdown、JSONL、CSV 与复核清单输出。
- 增加内置 Python 运行环境和 PaddleOCR 模型，正常使用无需额外下载。
- 增加 `启动工具.bat` 双击启动入口。
- GUI 增加“包含子文件夹”的说明文字。
- GUI 增加可选的“在输出文件夹中新建子文件夹”功能。
- GUI 增加 Windows DPI awareness 设置，改善高缩放屏幕下的显示清晰度。
- GUI 增加实时进度条、已完成/剩余数量和当前文件名显示。
- 增加 `启动工具.vbs` 无终端启动入口，双击后只显示工具窗口。
- 默认 OCR 后端从 PaddleOCR 切换为 RapidOCR + ONNXRuntime，显著提升 Windows 本地识别速度。
- 静默 OCR 引擎日志，减少控制台输出干扰。

### Changed

- 项目目录改名为 `batch-image-to-text`。
- GUI 启动脚本改为直接使用内置运行环境。
- 禁用 MKLDNN/oneDNN，以规避 Windows CPU 推理兼容问题。
- GUI 调整为温暖卡片式视觉布局，优化默认窗口比例、控件对齐、按钮间距和标题显示。
- GUI 的“选择”按钮恢复黑色系，“开始提取”按钮使用参考图橙色系。
