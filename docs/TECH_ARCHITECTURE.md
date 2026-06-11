# Technical Architecture

## 总体架构

工具分为输入层、OCR 层、导出层和展示层。

```text
图片文件夹 -> 图片扫描 -> OCR 识别 -> 结构化记录 -> Markdown/JSONL/CSV/复核清单
```

## 模块拆分

- `src/app.py`：GUI 和命令行入口。
- `src/ocr_engine.py`：OCR 引擎封装。
- `src/exporters.py`：结果文件导出。
- `src/models.py`：识别结果数据结构。

## 技术栈选择

- Python：适合本地文件处理和 GUI。
- Tkinter：Python 内置 GUI，不增加额外界面依赖。
- RapidOCR + ONNXRuntime：当前默认 OCR 后端，Windows 本地 CPU 识别速度更快。
- Pillow：图片基础读取和格式检查。
- 内置 `runtime/python`：保证工具不依赖系统 Python。
- 内置 `models/paddlex`：保证工具正常使用时不再额外下载 OCR 模型。

## 数据流

1. 用户选择输入文件夹。
2. 程序扫描图片文件。
3. OCR 引擎逐张识别。
4. 生成 `OcrRecord`。
5. 导出结果文件。

## 输入输出格式

输入：图片路径列表。

输出：

- Markdown：人类阅读。
- JSONL：后续程序处理。
- CSV：总览索引。
- Review Markdown：人工复核。

## 是否需要数据库

当前 MVP 不需要数据库。

## 是否需要 API

当前 MVP 不需要外部 API，也不会上传图片。

## 哪些部分由代码完成

- 文件扫描。
- OCR 调用。
- 状态标注。
- 结果导出。

## 哪些部分由 AI 模型完成

当前 MVP 不调用 AI 模型。后续可以增加“基于 OCR 原文的清洗归类”模块。

## 错误处理

- OCR 依赖缺失时给出安装提示。
- 单张图片失败时记录错误，不中断整个批次。
- 空结果和低置信度结果写入复核清单。
- 启动脚本会检查内置 Python 和 OCR 模型是否存在。

## 后续扩展接口

- 可新增 `VisionModelOcrEngine`，用于高精度复核。
- 可新增 `TextCleaner`，用于后续知识点清洗。
