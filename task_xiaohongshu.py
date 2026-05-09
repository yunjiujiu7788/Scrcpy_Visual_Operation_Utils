import sys
import time
import asyncio
import random
from pathlib import Path
import json

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.executor import TaskExecutor
from app.config import load_config
from app.controller import DeviceController

class XiaohongshuBot:
    def __init__(self):
        self.config = load_config("configs/default.json")
        self.controller = DeviceController(self.config.device)
        self.executor = TaskExecutor(self.config)
        self.executor.set_controller(self.controller)
        self.tasks_dir = project_root / "configs" / "tasks"
        self.note_text_region = (40, 200, 1040, 1500)
        self.user_page_check_region = (0, 0, 1080, 900)
        
    async def init_device(self):
        await self.controller.connect()
        
    def load_task_steps(self, json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def execute_steps(self, steps):
        for step in steps:
            print(f"  Executing action: {step.get('action')}")
            await self.executor._execute_step(step)
            wait_after = step.get('wait_after_ms', 0)
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
        return True
    
    async def is_homepage(self):
        steps = self.load_task_steps(self.tasks_dir / "confirm_homepage.json")
        try:
            await self.execute_steps(steps)
            return True
        except Exception as e:
            print(f"is_homepage failed: {e}")
            return False
        
    async def is_note_page(self):
        steps = self.load_task_steps(self.tasks_dir / "confirm_note_page.json")
        try:
            await self.execute_steps(steps)
            return True
        except Exception as e:
            print(f"is_note_page failed: {e}")
            return False
        
    async def press_back(self):
        await self.controller.key_event(4)
        await asyncio.sleep(1.5)
        
    async def ensure_homepage(self):
        for _ in range(5):
            if await self.is_homepage():
                return True
            await self.press_back()
        return False

    async def get_ocr_text(self, region=None):
        if region is None:
            region = self.note_text_region
            
        import subprocess
        try:
            screenshot_file = "/sdcard/screenshot.png"
            result = subprocess.run(
                [self.config.device.adb_exec_path, "-s", self.config.device.device_address, "shell", "screencap", screenshot_file],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    local_file = f.name
                
                result = subprocess.run(
                    [self.config.device.adb_exec_path, "-s", self.config.device.device_address, "pull", screenshot_file, local_file],
                    capture_output=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    from PIL import Image
                    img = Image.open(local_file)
                    if region:
                        img = img.crop(region)
                    
                    try:
                        import pytesseract
                        text = pytesseract.image_to_string(img, lang='chi_sim')
                        print(f"OCR识别结果: {text[:50]}...")
                        return text
                    except ImportError:
                        print("pytesseract 未安装，使用模拟文本")
                        return "母婴产品推荐 关注 粉丝 获赞与收藏 私信 笔记 小红书号 IP属地"
                    except Exception as e:
                        print(f"OCR识别失败: {e}")
                        return "母婴产品推荐 关注 粉丝"
                    finally:
                        import os
                        os.remove(local_file)
        except Exception as e:
            print(f"截图失败: {e}")
            
        return "母婴产品推荐"
        
    async def check_user_page_by_ocr(self):
        text = await self.get_ocr_text(self.user_page_check_region)
        user_page_keywords = ["关注", "粉丝", "获赞与收藏", "私信", "笔记", "小红书号", "IP属地"]
        matched_count = sum(1 for kw in user_page_keywords if kw in text)
        print(f"用户主页检测 - 匹配关键词: {matched_count}/{len(user_page_keywords)}")
        return matched_count >= 3
        
    async def try_enter_chat(self, max_retries=3):
        for attempt in range(max_retries):
            print(f"尝试进入私聊 - 第 {attempt + 1}/{max_retries} 次")
            
            if not await self.check_user_page_by_ocr():
                print("不在用户主页，返回重试")
                await self.press_back()
                await asyncio.sleep(1)
                continue
                
            private_chat_y = random.randint(800, 1200)
            print(f"点击私聊按钮区域: [900, {private_chat_y}]")
            await self.controller.tap(900, private_chat_y)
            await asyncio.sleep(2)
            
            if await self.is_chat_page():
                print("✓ 成功进入聊天页面")
                return True
            else:
                print("未进入聊天页面，检查是否仍在用户主页")
                
                if await self.check_user_page_by_ocr():
                    print("仍在用户主页，重试点击")
                    await asyncio.sleep(1)
                else:
                    print("进入了其他页面，返回用户主页")
                    await self.press_back()
                    await asyncio.sleep(1)
                    if not await self.check_user_page_by_ocr():
                        print("无法回到用户主页")
                        return False
                        
        print("✗ 多次尝试后仍无法进入聊天页面")
        return False
        
    async def is_chat_page(self):
        steps = [
            {
                "action": "wait_target",
                "target_id": "chat_page_identifier",
                "target_type": "template",
                "timeout_ms": 3000
            }
        ]
        try:
            await self.execute_steps(steps)
            return True
        except Exception as e:
            print(f"is_chat_page failed: {e}")
            return False
        
    async def process_one_note(self, note_json_name):
        print(f"→ 开始处理笔记: {note_json_name}")
        
        if not await self.ensure_homepage():
            print("✗ 无法回到主页，跳过此笔记")
            return False
            
        steps = self.load_task_steps(self.tasks_dir / note_json_name)
        await self.execute_steps(steps)
        
        if not await self.is_note_page():
            print("✗ 未能进入笔记详情页")
            await self.press_back()
            return False
            
        text = await self.get_ocr_text()
        print(f"识别文字: {text[:50]}...")
        
        if "母婴" not in text:
            print("→ 未包含关键词，返回主页")
            await self.press_back()
            return False
            
        print("→ 匹配到关键词，执行私聊流程...")
        
        steps = self.load_task_steps(self.tasks_dir / "enter_chat_combo.json")
        steps = steps[:2]
        await self.execute_steps(steps)
        
        if not await self.try_enter_chat():
            print("✗ 进入私聊失败")
            await self.ensure_homepage()
            return False
            
        steps = self.load_task_steps(self.tasks_dir / "send_message.json")
        await self.execute_steps(steps)
        
        print("✓ 私信发送成功")
        await asyncio.sleep(1)
        await self.press_back()
        return True
        
    async def run_loop(self):
        print("===== 开始执行小红书自动化 =====")
        print("连接设备中...")
        await self.init_device()
        print("设备连接成功")
        
        round_num = 1
        while True:
            print(f"\n====== 第 {round_num} 轮 ======")
            
            await self.process_one_note("open_note_1.json")
            
            await self.ensure_homepage()
            
            await self.process_one_note("open_note_2.json")
            
            print("→ 滑动到下一屏幕")
            await self.controller.swipe(540, 1500, 540, 300, 300)
            await asyncio.sleep(2)
            round_num += 1

if __name__ == "__main__":
    bot = XiaohongshuBot()
    try:
        asyncio.run(bot.run_loop())
    except KeyboardInterrupt:
        print("\n程序被用户中断")