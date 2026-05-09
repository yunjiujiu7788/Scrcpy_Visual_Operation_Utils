# Scrcpy 视觉操作通用工具 —— AI 开发任务书

> **项目目标**：基于 MaaFramework，构建一个可通过 **JSON 配置** 全自动操作安卓设备（通过 scrcpy 获取画面）的通用工具。  
> **核心理念**：用户只需定义 JSON 字段，工具即按照字段执行对应的识图与操作，无需修改代码。  
> **交付要求**：完整可运行的 Python 项目，结构清晰，采用当前主流的架构模式。

## 1. 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 语言 | Python 3.11+ | 与 MaaFramework 官方要求一致 |
| 设备控制 | **MaaFramework** (Python 绑定) | 提供截图、点击、滑动、按键等底层能力 |
| 图像匹配 | OpenCV (cv2) | 模板匹配、特征点匹配 |
| OCR 文字识别 | PaddleOCR | 可选，用于识别屏幕文字 |
| 配置管理 | Pydantic v2 | 严格校验 JSON 字段，防止配置错误 |
| 异步调度 | asyncio | 任务可并发、可中断，不阻塞主流程 |
| 日志 | loguru | 更友好的日志输出 |

## 2. 项目结构 (推荐)
```
scrcpy-vision-tool/
├── app/
│ ├── main.py # 启动入口，加载配置并启动任务
│ ├── config.py # 所有配置的 Pydantic 模型
│ ├── controller.py # 封装 MaaFramework 控制器
│ ├── recognizer/ # 识别器模块
│ │ ├── base.py # 识别器基类
│ │ ├── template_matcher.py # 图像模板匹配
│ │ ├── ocr_recognizer.py # OCR 文字识别
│ │ └── feature_matcher.py # SIFT/ORB 特征匹配
│ ├── actions/ # 动作执行器
│ │ ├── base.py
│ │ ├── tap.py
│ │ ├── swipe.py
│ │ ├── text_input.py
│ │ └── wait.py
│ ├── task_runner.py # 任务调度器，解析 JSON 并顺序执行
│ └── utils/
│ ├── image.py # 截图、图像预处理
│ └── adb_utils.py # ADB 辅助函数（备用）
├── configs/
│ └── task_example.json # 示例任务 JSON
├── images/ # 存放所有匹配模板图
├── logs/ # 运行日志
├── requirements.txt
├── .env
└── README.md
```

## 3. 核心流程
读取JSON配置 → 连接MaaFramework控制器 → 循环/按顺序执行每个任务
| |
v v
(每个步骤)获取当前截图 → 调用对应识别器找到目标 → 获得坐标 → 执行动作 → 等待后继续

- **异步设计**：整个任务运行在一个异步循环中，避免截图时卡住 GUI。
- **错误处理**：识别失败时自动重试，超过阈值则记录日志并跳过/退出。

## 4. JSON 配置格式设计

这是整个工具的“语言”，用户通过 JSON 定义“看什么”和“做什么”。

### 4.1 顶层结构

```json
{
  "device": {
    "adb_path": "127.0.0.1:5555",
    "screenshot_quality": 30
  },
  "targets": [ ... ],
  "tasks": [ ... ]
}
```
### 4.2 `targets` 定义（识别目标，可复用）
```json
{
  "target_id": "btn_confirm",           // 唯一ID，动作中通过它引用
  "type": "template",                   // 识别类型：template / ocr / feature / coordinate
  "image_path": "imgs/confirm.png",     // template类型必填
  "text": "确认",                        // ocr类型必填
  "roi": [500, 800, 200, 100],          // 可选，限定识别区域 [x, y, w, h]
  "threshold": 0.85                     // 匹配阈值，默认0.8
}
```
支持的 type：

- **`template`**：图像模板匹配（OpenCV matchTemplate）
- **`ocr`**：文字识别，需指定 `text`
- **`feature`**：特征点匹配（SIFT/ORB）
- **`coordinate`**：直接指定固定坐标（用于不需要识别的情况）

### 4.3 `tasks` 定义（动作序列）

```json
{
  "task_name": "自动登录",
  "trigger": "on_start",                // on_start / on_schedule / manual
  "cron": null,                          // 定时的cron表达式(可选)
  "steps": [
    {
      "action": "tap",                  // 动作类型
      "target_id": "btn_login",         // 引用 target
      "offset": [10, 20],               // 可选，坐标微调
      "wait_before_ms": 500,
      "wait_after_ms": 1500
    },
    {
      "action": "wait_target",
      "target_id": "txt_welcome",       // 等待某个目标出现再继续
      "timeout_ms": 10000
    },
    {
      "action": "swipe",
      "start_coord": [100, 800],
      "end_coord": [100, 200],
      "duration_ms": 300
    }
  ]
}
```
支持的动作类型：

- **`tap`**：点击目标中心
- **`swipe`**：滑动
- **`long_press`**：长按
- **`input_text`**：输入文字
- **`key_event`**：发送按键码（如 BACK、HOME）
- **`wait_target`**：等待目标出现（超时则跳过/报错）
- **`wait_ms`**：纯粹等待

## 5. 架构实现要点（AI Agent 需实现的代码逻辑）
### 5.1 配置模型 (`app/config.py`)
使用 Pydantic 严格定义上述 JSON 结构，自动校验。例如：
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Target(BaseModel):
    target_id: str
    type: Literal["template", "ocr", "feature", "coordinate"]
    image_path: Optional[str] = None
    text: Optional[str] = None
    roi: Optional[list] = None
    threshold: float = 0.8

class Step(BaseModel):
    action: Literal["tap", "swipe", ...]
    target_id: Optional[str] = None
    wait_before_ms: int = 0
    wait_after_ms: int = 500
    # ...其他字段

class Task(BaseModel):
    task_name: str
    trigger: Literal["on_start", "on_schedule", "manual"]
    cron: Optional[str] = None
    steps: List[Step]

class Config(BaseModel):
    device: DeviceConfig
    targets: List[Target]
    tasks: List[Task]
```
### 5.2 控制器封装 (`app/controller.py`)
基于 MaaFramework 的 `AdbController`：

```python
from maa.controller import AdbController

class DeviceController:
    def __init__(self, adb_path: str):
        self.ctrl = AdbController(
            adb_path=adb_path,
            screencap_method="fast",
            input_method="adb"
        )
    
    def screencap(self) -> np.ndarray:
        # 调用 self.ctrl.post_screencap()，获得图片并转换为 cv2 格式
        ...

    def tap(self, x: int, y: int):
        self.ctrl.post_tap(x, y).wait()

    def swipe(self, start, end, duration):
        ...

    def input_text(self, text: str):
        ...
```
### 5.3 识别器实现
模板匹配 (`template_matcher.py`)：使用 `cv2.matchTemplate`，支持指定阈值和 ROI。
OCR 识别 (`ocr_recognizer.py`)：若使用 PaddleOCR，识别全图文字，返回包含指定文字的坐标区域。
特征匹配 (`feature_matcher.py`)：SIFT/ORB，适用于不同分辨率或轻微形变场景。
所有识别器都遵循同一接口：
```python
class BaseRecognizer:
    def locate(self, target: Target, screenshot: np.ndarray) -> Optional[Tuple[int, int]]:
        # 返回像素坐标 (x, y) 中心点，未找到返回 None
        raise NotImplementedError
```
5.4 任务调度器 (`app/task_runner.py`)
负责：

读取配置
- 根据 `trigger` 决定启动方式（立即运行或定时运行）
- 遍历 `steps`，调用识别器和动作执行器
- 处理超时、失败重试

核心逻辑示意：
```python
async def run_task(task: Task, controller, recognizers):
    for step in task.steps:
        # 1. 可选的 wait_before_ms
        await asyncio.sleep(step.wait_before_ms / 1000)
        
        # 2. 截取当前屏幕
        img = await controller.screencap()
        
        # 3. 如果步骤引用了 target，则进行识别
        coord = None
        if step.target_id:
            target = find_target_by_id(task.targets, step.target_id)
            recognizer = recognizers[target.type]
            coord = recognizer.locate(target, img)
            if coord is None:
                # 重试逻辑...
                raise Exception(f"识别失败: {target.target_id}")
        
        # 4. 执行动作
        if step.action == "tap":
            controller.tap(coord[0], coord[1])
        elif step.action == "swipe":
            ...
        
        # 5. 等待 wait_after_ms
        await asyncio.sleep(step.wait_after_ms / 1000)
```
### 5.5 主程序入口 (`app/main.py`)

```python
import asyncio
from app.config import load_config
from app.controller import DeviceController
from app.task_runner import run_all_tasks

async def main():
    config = load_config("configs/task_example.json")
    controller = DeviceController(config.device.adb_path)
    await run_all_tasks(config, controller)

if __name__ == "__main__":
    asyncio.run(main())
```
## 6. 提供给 AI Agent 的开发指令

当使用 OpenClaw 等工具时，可下达以下逐步指令（粘贴文档时附带）：

1. 按照“项目结构”创建所有文件和目录。

2. 先在 `requirements.txt` 中写入依赖：`maa-framework`, `pydantic`, `opencv-python`, `numpy`, `loguru, paddleocr`（可选）。

3. 实现 `app/config.py`，严格按照第4节的 JSON 格式定义 Pydantic 模型，并实现从 JSON 文件加载为 `Config` 对象的函数。

4. 实现 `app/controller.py`，封装 MaaFramework 的 AdbController，提供 `screencap`, `tap`, `swipe` 等异步方法。

5. 实现 `app/recognizer/` 下的识别器，至少完成 `template_matcher` 和 `ocr_recognizer`，均继承 `BaseRecognizer`。

6. 实现 `app/actions/` 下的动作执行器（可以合并到 task_runner 中，但建议分离）。

7. 实现 `app/task_runner.py`，支持顺序执行任务步骤，健壮的错误处理。

8. 完成 `app/main.py`，让工具能通过命令行读取 JSON 路径并启动。

9. 编写一个 `configs/task_example.json`，演示如何配置一个简单的“打开设置并返回”的任务。

10. 确保所有异步操作正确使用 `await`，控制器方法如果是同步的需用 `asyncio.to_thread` 包装。

## 7. 扩展性考虑
- AI 动态决策：未来可在任务步骤中增加 ai_decision 动作，将截图发送给多模态大模型，根据返回的动作指令执行（但当前版本先不做）。
- GUI 配置界面：可基于 Pydantic 自动生成表单，方便非程序员使用。
- 分布式：工具本身是单机运行，可考虑通过 WebSocket 暴露接口，让其他系统下发任务。

8. 注意事项
MaaFramework 的 Python 绑定文档可参考 MaaFramework 官方文档。

截屏方式：建议使用 MaaFramework 自带的 screencap 接口，兼容性最好。

坐标系统：所有坐标均为 scrcpy 画面分辨率（通常与手机屏幕一致），无需额外转换。


