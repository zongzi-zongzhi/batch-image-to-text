# Project Structure

## `src/`

保存可运行代码。

## `src/app.py`

提供 GUI 和命令行入口。

## `src/ocr_engine.py`

封装 OCR 识别逻辑。当前使用 PaddleOCR。

## `src/exporters.py`

负责把识别结果导出为 Markdown、JSONL、CSV 和复核清单。

## `src/models.py`

定义单张图片的 OCR 结果结构。

## `docs/`

保存产品需求、技术架构、项目结构和开发日志。

## `tests/`

保存最小测试。

## `examples/`

保存示例输入输出说明。

## `scripts/`

保存启动脚本。

## `runtime/`

保存内置 Python 运行环境和依赖。正常使用不需要系统额外安装 Python。

## `models/`

保存内置 OCR 模型。正常使用不需要额外下载模型。

## `启动工具.bat`

双击启动 GUI 工具。
