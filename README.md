# Scrcpy 视觉操作通用工具

基于 MaaFramework + OpenCV + YOLO-World 的手机视觉自动化框架，支持模板匹配、OCR 识别和 AI 目标检测。

## 主要功能

- **模板匹配**: 基于 OpenCV 的图像识别
- **OCR 识别**: EasyOCR 文字识别
- **AI 检测**: YOLO-World 实时目标检测
- **自动化执行**: MaaFramework 任务编排与执行

## 项目结构

```
Scrcpy_Visual_Operation_Utils/
├── main.py                     # 主入口
├── task_xiaohongshu.py         # 小红书自动化主控脚本
├── test_yolo_world.py          # YOLO-World 检测测试
├── train_yolo.py               # YOLO 模型训练脚本
├── label_tool.py               # 本地标签工具
├── web_label_tool.py           # Web 标签工具
├── requirements.txt            # Python 依赖
├── README.md
│
├── configs/                    # 任务配置
│   ├── default.json            # 默认配置
│   ├── example_task.json       # 示例任务
│   └── tasks/                  # 原子操作任务
│       ├── confirm_homepage.json
│       ├── confirm_note_page.json
│       ├── open_note_1.json
│       ├── open_note_2.json
│       ├── enter_chat_combo.json
│       └── send_message.json
│
├── datasets/                   # 训练数据集
│   └── xiaohongshu/            # 小红书数据集
│       ├── images/
│       │   ├── train/          # 训练图片
│       │   ├── val/            # 验证图片
│       │   └── test/           # 测试图片
│       ├── labels/             # YOLO 格式标签
│       └── data.yaml           # 数据集配置
│
├── app/                        # 核心模块
│   ├── config.py               # 配置模型 (Pydantic v2)
│   ├── controller.py           # 设备控制器 (MaaFramework)
│   ├── executor.py             # 任务执行器
│   └── utils/
│       └── log_setup.py        # 日志配置 (loguru)
│
├── images/                     # 模板图片目录
├── logs/                       # 日志和截图输出
└── runs/                       # 训练输出目录
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 ADB

确保已安装 Android SDK 并配置环境变量：

```bash
adb devices
```

### 3. 运行程序

```bash
# YOLO-World 检测测试
python test_yolo_world.py

# 小红书自动化
python task_xiaohongshu.py

# 主程序
python main.py
```

## 小红书自动化

### 功能说明

自动浏览小红书笔记，识别包含"母婴"关键词的内容，并发送私信。

### 运行方式

```bash
python task_xiaohongshu.py
```

按 `Ctrl+C` 中断循环。

### 流程说明

1. 确认小红书主页
2. 点击笔记进入详情
3. OCR 识别笔记内容
4. 判断是否包含"母婴"关键词
5. 进入用户主页 → 点击私聊 → 发送消息
6. 返回主页处理下一篇笔记
7. 滑动屏幕循环执行

## YOLO-World 检测

### 功能说明

使用 YOLO-World 进行实时目标检测，支持自定义训练模型。

### 运行方式

```bash
python test_yolo_world.py
```

### 模型说明

- 自动搜索 `runs/train/**/best.pt` 或 `runs/detect/**/best.pt`
- 支持指定模型路径初始化
- 无模型时使用 YOLO-World 预训练模型

## 模型训练

### 准备数据集

```
datasets/
└── xiaohongshu/
    ├── images/
    │   ├── train/      # 训练图片
    │   └── val/        # 验证图片
    ├── labels/         # YOLO 格式标签 (.txt)
    └── data.yaml       # 数据集配置
```

### 标签格式

每行格式：`class_id x_center y_center width height`（归一化值）

### 开始训练

```bash
python train_yolo.py
```

## 配置说明

### 设备配置 (configs/default.json)

```json
{
  "device": {
    "adb_exec_path": "C:\\Android\\platform-tools\\adb.exe",
    "device_address": "3f44fd1a",
    "screenshot_quality": 30,
    "screencap_method": "fast",
    "input_method": "adb"
  }
}
```

### 目标类型

| 类型 | 说明 | 依赖 |
|------|------|------|
| `template` | 模板匹配 | 模板图片 (PNG) |
| `ocr` | 文字识别 | EasyOCR |
| `yolo` | YOLO 检测 | YOLO 模型 |
| `coordinate` | 固定坐标 | 无 |

### 动作类型

| 动作 | 参数 | 说明 |
|------|------|------|
| `tap` | `target_id`, `offset` | 点击 |
| `swipe` | `start_coord`, `end_coord`, `duration_ms` | 滑动 |
| `long_press` | `target_id`, `duration_ms` | 长按 |
| `input_text` | `text` | 文字输入 |
| `key_event` | `keycode` | 按键事件 |
| `wait_target` | `target_id`, `timeout_ms` | 等待目标 |
| `wait_ms` | `duration_ms` | 等待固定时长 |

## 模板图片

需准备以下模板图片放入 `images/` 目录：

| 图片名称 | 用途说明 |
|---------|---------|
| `homepage_identifier.png` | 小红书主页标识 |
| `note_detail_identifier.png` | 笔记详情页标识 |
| `chat_page_identifier.png` | 聊天界面特征图片 |

## 日志

日志输出到 `logs/` 目录：
- `app_YYYY-MM-DD.log`: 全部日志
- `error_YYYY-MM-DD.log`: 错误日志
- `screenshots/`: 截图记录

## 技术栈

- **框架**: MaaFramework (MaaFw >= 5.0.0)
- **配置**: Pydantic v2
- **图像处理**: OpenCV
- **目标检测**: Ultralytics YOLO-World
- **OCR**: EasyOCR
- **日志**: loguru
- **异步**: asyncio

## 注意事项

1. 确保手机已开启 USB 调试模式
2. 首次运行需要授权 ADB 连接
3. 建议使用 scrcpy 查看手机屏幕：`scrcpy --no-audio`
4. OCR 功能需要 EasyOCR（如未安装会自动使用模拟模式）
5. YOLO-World 需要 ultralytics（如未安装会自动使用模拟模式）

## 更新日志

### 2026-05-11
- 添加 YOLO-World 真实设备截图支持
- 添加图像分析检测功能
- 支持自定义训练模型加载

### 2026-05-10
- 添加 YOLO-World 检测功能
- 支持小红书笔记卡片检测

### 2026-05-09
- 完成小红书自动化功能
- 添加 OCR 关键词匹配
