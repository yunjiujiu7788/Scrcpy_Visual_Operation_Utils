
> 1.识别是否在小红书主页（template	模板匹配）→2. 识别并点击笔记→3. 识别是否在笔记界面→4. 截图并提取文字→4. 判断是否包含“母婴”（不包含则执行scrcpy.exe的返回进入步骤12）→5. 点击用户头像→6. 识别是否在用户主页界面→7. 点击私聊按钮→8. 识别是否在用户私聊界面→9. 点击对话框→10. 输入内容→11. 点击发送→12. 执行scrcpy.exe的返回→13. 识别是否在小红书主页（没有则执行scrcpy.exe的返回）→14. 点击另一指定位置笔记→15. 识别是否在笔记界面→16. 截图并提取文字→17. 判断是否包含“母婴”（不包含则执行scrcpy.exe的返回进入步骤27）→18. 点击用户头像→19. 识别是否在用户主页界面→20. 点击私聊按钮→21. 识别是否在用户私聊界面→22. 点击对话框→23. 输入内容→24. 点击发送→25. 执行scrcpy.exe的返回→26. 识别是否在小红书主页（没有则执行scrcpy.exe的返回）→27. 向下滑动，重复执行

以下步骤为ai生成，需结合项目情况和实际流程情况构建

## 第一步：需要创建的文件清单
需要新建两个目录，并添加以下文件：

```
configs/tasks/          # 存放原子操作JSON
├── confirm_homepage.json   # 确认主页
├── open_note_1.json        # 点击左上角笔记
├── open_note_2.json        # 点击另一指定笔记
├── confirm_note_page.json  # 确认笔记界面
├── enter_chat_combo.json   # 进主页+点私聊(组合动作链)
└── send_message.json       # 输入内容+发送
task_xiaohongshu.py         # 主控脚本，放项目根目录
```

## 第二步：逐个编写原子操作JSON
这些JSON直接对应你项目支持的格式，可以直接被 `executor` 加载运行。你需要根据实际截图的坐标或模板图片名，替换掉 `` 中的占位符。

1. `confirm_homepage.json` (等待小红书的“推荐”或“首页”标识出现，用于确认)

```json
[
  {
    "action": "wait_target",
    "params": {
      "target_id": "homepage_identifier",
      "target_type": "template",
      "timeout_ms": 5000
    }
  }
]
```
2. `open_note_1.json` (点击左上角笔记封面)

```json
[
  {
    "action": "tap",
    "params": {
      "target_type": "coordinate",
      "start_coord": [100, 250]
    }
  }
]
```

3. `confirm_note_page.json` (确认已进入笔记详情)

```json
[
  {
    "action": "wait_target",
    "params": {
      "target_id": "note_detail_identifier",
      "target_type": "template",
      "timeout_ms": 5000
    }
  }
]
```
4. `enter_chat_combo.json` (组合动作：点用户头像 → 确认主页 → 点私聊 → 确认私聊窗口)

```json
[
  {
    "action": "tap",
    "params": {
      "target_id": "author_avatar",
      "target_type": "template",
      "offset": [0, 0]
    }
  },
  {
    "action": "wait_target",
    "params": {
      "target_id": "user_page_identifier",
      "target_type": "template",
      "timeout_ms": 5000
    }
  },
  {
    "action": "tap",
    "params": {
      "target_id": "private_chat_btn",
      "target_type": "template",
      "offset": [0, 0]
    }
  },
  {
    "action": "wait_target",
    "params": {
      "target_id": "chat_input_box",
      "target_type": "template",
      "timeout_ms": 5000
    }
  }
]
```
5. `send_message.json` (此处文字需要变成变量传入，建议在脚本中动态修改或在动作引擎中临时替换。最简方式：先固定文本，后面在脚本里用更灵活的方式调用)

```json
[
  {
    "action": "tap",
    "params": {
      "target_id": "chat_input_box",
      "target_type": "template"
    }
  },
  {
    "action": "input_text",
    "params": {
      "text": "你好，我对母婴产品很感兴趣..."
    }
  },
  {
    "action": "tap",
    "params": {
      "target_id": "send_button",
      "target_type": "template"
    }
  }
]
```

## 第三步：编写主控脚本 `task_xiaohongshu.py`
Python层面串联逻辑、判断和重试。
```python
import sys
import time
from pathlib import Path

# 把项目根目录加入路径，确保能导入你的模块
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.executor import TaskExecutor
from app.recognizer.ocr_recognizer import OCRRecognizer
from app.utils import screenshot
from app.actions.engine import ActionEngine
from app.controller import DeviceController
import configs.default as default_config

class XiaohongshuBot:
    def __init__(self):
        # 初始化核心组件
        self.controller = DeviceController(default_config.device)
        self.executor = TaskExecutor(self.controller)
        self.ocr = OCRRecognizer()
        self.action_engine = ActionEngine(self.controller)
        self.note_text_region = (40, 200, 1040, 1500) 
        
        self.tasks_dir = project_root / "configs" / "tasks"
        
    def is_homepage(self):
        """执行JSON任务，用模板匹配检查是否在主页"""
        return self.executor.run_task_from_json(self.tasks_dir / "confirm_homepage.json")
        
    def is_note_page(self):
        return self.executor.run_task_from_json(self.tasks_dir / "confirm_note_page.json")
        
    def press_back(self):
        """模拟Android返回键"""
        self.action_engine.execute({
            "action": "key_event",
            "params": {"keycode": "KEYCODE_BACK"}
        })
        time.sleep(1.5)
        
    def ensure_homepage(self):
        """如果不是主页，就按返回直到回到主页"""
        for _ in range(5): # 最多重试5次
            if self.is_homepage():
                return True
            self.press_back()
        return False

    def get_ocr_text(self, region=None):
        """截图并裁剪指定区域后OCR识别，返回文字"""
        if region is None:
            region = self.note_text_region  # 默认使用笔记文字区域
        
        # 1. 截图全屏
        screenshot_path = "logs/temp_screenshot.png"
        self.controller.screencap()  # 假设控制器有方法保存到logs目录
        # 如果screencap()直接保存到了logs/screenshots/里，需要你处理一下路径
        # 这里假设可以获取到最新截图的路径
        
        # 2. 用PIL裁剪
        img = Image.open(screenshot_path)
        cropped_img = img.crop(region)  # (left, upper, right, lower)
        crop_path = "logs/temp_crop.png"
        cropped_img.save(crop_path)
        
        # 3. 使用裁剪后的图片做OCR
        results = self.ocr.recognize(crop_path)
        all_text = "".join([r["text"] for r in results])
        return all_text
        
    def process_one_note(self, note_json_name):
        """处理单个笔记的完整流程，返回是否成功发送了私信"""
        print(f"→ 开始处理笔记: {note_json_name}")
        
        # 1. 确保在主页
        if not self.ensure_homepage():
            print("✗ 无法回到主页，跳过此笔记")
            return False
            
        # 2. 点击笔记
        self.executor.run_task_from_json(self.tasks_dir / note_json_name)
        time.sleep(2)
        
        # 3. 确认笔记界面
        if not self.is_note_page():
            print("✗ 未能进入笔记详情页")
            self.press_back()
            return False
            
        # 4. 截图识别文字
        text = self.get_ocr_text()
        print(f"识别文字: {text[:50]}...")  # 打印前50字
        
        # 5. 核心判断：是否包含“母婴”
        if "母婴" not in text:
            print("→ 未包含关键词，返回主页")
            self.press_back()
            return False
            
        # 6-8. 进入用户主页并私聊 (组合JSON)
        print("→ 匹配到关键词，执行私聊流程...")
        success = self.executor.run_task_from_json(self.tasks_dir / "enter_chat_combo.json")
        if not success:
            print("✗ 进入私聊失败")
            self.ensure_homepage()
            return False
            
        # 9-11. 发送消息 (这里用动作引擎直接发送，更灵活)
        self.action_engine.execute({"action": "tap", "params": {"target_id": "chat_input_box", "target_type": "template"}})
        time.sleep(0.5)
        # 直接调用adb input text更稳定
        self.controller.adb.shell("input text", "你好，在吗？我是母婴博主") 
        self.action_engine.execute({"action": "tap", "params": {"target_id": "send_button", "target_type": "template"}})
        
        print("✓ 私信发送成功")
        time.sleep(1)
        self.press_back() # 从私聊界面返回
        return True
        
    def run_loop(self):
        """主循环：轮询两本笔记，然后向下滑动"""
        print("===== 开始执行小红书自动化 =====")
        round_num = 1
        while True:
            print(f"\n====== 第 {round_num} 轮 ======")
            
            # 处理笔记1
            self.process_one_note("open_note_1.json")
            
            # 再次确保在主页
            self.ensure_homepage()
            
            # 处理笔记2
            self.process_one_note("open_note_2.json")
            
            # 步骤27：向下滑动
            print("→ 滑动到下一屏幕")
            self.action_engine.execute({
                "action": "swipe",
                "params": {
                    "start_coord": [540, 1500],
                    "end_coord": [540, 300],
                    "duration_ms": 300
                }
            })
            time.sleep(2)
            round_num += 1
            
            # 这里可以加一个退出条件，比如按下Ctrl+C中断循环

if __name__ == "__main__":
    bot = XiaohongshuBot()
    try:
        bot.run_loop()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
```


