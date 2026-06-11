$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path "runtime\python\python.exe")) {
  throw "未找到内置 Python：runtime\python\python.exe"
}

if (-not (Test-Path "runtime\python\Lib\site-packages\rapidocr")) {
  throw "未找到内置 OCR 引擎：runtime\python\Lib\site-packages\rapidocr"
}

if (-not (Test-Path "runtime\python\Lib\site-packages\onnxruntime")) {
  throw "未找到内置 OCR 运行库：runtime\python\Lib\site-packages\onnxruntime"
}

.\runtime\python\pythonw.exe -m src.app
