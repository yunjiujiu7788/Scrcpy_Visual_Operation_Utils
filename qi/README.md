# Scrcpy 视觉操作通用工具

基于 MaaFramework + OpenCV + PaddleOCR 的手机视觉自动化框架。

## 项目结构

```
D:\pycharmobject\Scrcpy 视觉操作通用工具\
├── main.py                      # 主入口
├── requirements.txt             # Python 依赖
├── start.bat                    # Windows 启动脚本
├── .env                         # 环境变量配置
├── .gitignore
├── README.md
├── configs/
│   ├── default.json             # 默认配置
│   └── example_task.json        # 示例任务配置
├── images/                      # 模板图片目录
├── logs/                        # 日志和截图输出
├── app/
│   ├── config.py                # 配置模型 (Pydantic v2)
│   ├── controller.py            # 设备控制器 (MaaFramework AdbController)
│   ├── executor.py              # 任务执行器 (编排/重试)
│   ├── recognizer/
│   │   ├── base.py              # 识别器基类
│   │   ├── template_matcher.py  # 模板匹配识别 (OpenCV)
│   │   ├── ocr_recognizer.py    # OCR 识别 (PaddleOCR)
│   │   ├── feature_matcher.py   # 特征匹配识别 (SIFT/ORB)
│   │   └── engine.py            # 识别引擎 (统一调度)
│   ├── actions/
│   │   ├── base.py              # 动作基类
│   │   ├── tap.py               # 点击动作
│   │   ├── swipe.py             # 滑动动作
│   │   ├── text_input.py        # 文字输入
│   │   ├── wait.py              # 等待动作
│   │   ├── long_press.py        # 长按动作
│   │   ├── key_event.py         # 按键事件
│   │   └── engine.py            # 动作引擎 (统一调度)
│   └── utils/
│       ├── log_setup.py         # 日志配置 (loguru)
│       ├── screenshot.py        # 截图工具
│       └── keycode_constants.py # 按键码常量
└── scripts/
    └── capture_template.py      # 模板图片截取工具
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

> PaddleOCR 需要额外安装 paddlepaddle，详见 [PaddleOCR 官方文档](https://github.com/PaddlePaddle/PaddleOCR)

### 2. 连接设备

确保手机已通过 ADB 连接：

```bash
adb devices
# 或通过 scrcpy 无线连接:
adb connect 127.0.0.1:5555
```

### 3. 运行

```bash
# 使用默认配置
python main.py

# 指定任务
python main.py -t "启动应用"

# 指定配置文件
python main.py -c configs/example_task.json
```

## 配置说明

### 设备配置

```json
{
  "device": {
    "adb_path": "127.0.0.1:5555",
    "screenshot_quality": 30,
    "screencap_method": "fast",
    "input_method": "adb"
  }
}
```

也通过环境变量覆盖：

```bash
# .env
ADB_PATH=192.168.1.100:5555
SCREENSHOT_QUALITY=50
```

### 目标类型

| 类型 | 说明 | 依赖 |
|------|------|------|
| `template` | 模板匹配 | 模板图片 (PNG) |
| `ocr` | 文字识别 | PaddleOCR |
| `feature` | 特征匹配 | 模板图片 |
| `coordinate` | 固定坐标 | 无 |

### 动作类型

| 动作 | 参数 | 说明 |
|------|------|------|
| `tap` | `target_id`/`start_coord`, `offset` | 点击 |
| `swipe` | `start_coord`, `end_coord`, `duration_ms` | 滑动 |
| `long_press` | `target_id`, `duration_ms` | 长按 |
| `input_text` | `text` | 文字输入 |
| `key_event` | `keycode` | 按键事件 |
| `wait_target` | `target_id`, `timeout_ms` | 等待目标出现 |
| `wait_ms` | `duration_ms` | 等待固定时长 |

## 模板制作

```bash
# 截取全屏后交互裁剪
python scripts/capture_template.py

# 只截取全屏
python scripts/capture_template.py --no-crop
```

## 日志

日志输出到 `logs/` 目录：
- `app_YYYY-MM-DD.log`: 全部日志
- `error_YYYY-MM-DD.log`: 错误日志
- `screenshots/`: 截图记录（含失败时自动保存）
