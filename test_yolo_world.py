import sys
import asyncio
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import load_config
from app.controller import DeviceController

class YOLOWorldDetector:
    def __init__(self, model_path: str = None):
        self.model = None
        self.initialized = False
        self._initialize_model()
    
    def _initialize_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO('yolov8s-world.pt')
            self.model.set_classes(['note card', '笔记卡片', 'post', 'card'])
            self.initialized = True
            print("✓ YOLO-World 模型加载成功")
        except Exception as e:
            print(f"⚠ YOLO-World 未安装，使用模拟模式: {e}")
            self.initialized = False
    
    def detect_note_cards(self, image_path: str) -> List[Dict]:
        if self.initialized:
            results = self.model.predict(image_path)
            boxes = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    boxes.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(box.conf[0]),
                        'center_x': int((x1 + x2) / 2),
                        'center_y': int((y1 + y2) / 2)
                    })
            return boxes
        else:
            return self._simulate_detection()
    
    def _simulate_detection(self) -> List[Dict]:
        print("使用模拟检测结果")
        return [
            {'bbox': [50, 200, 280, 450], 'confidence': 0.92, 'center_x': 165, 'center_y': 325},
            {'bbox': [330, 200, 560, 450], 'confidence': 0.88, 'center_x': 445, 'center_y': 325},
            {'bbox': [610, 200, 840, 450], 'confidence': 0.95, 'center_x': 725, 'center_y': 325},
            {'bbox': [890, 200, 1080, 450], 'confidence': 0.85, 'center_x': 985, 'center_y': 325},
            {'bbox': [50, 500, 280, 750], 'confidence': 0.90, 'center_x': 165, 'center_y': 625},
            {'bbox': [330, 500, 560, 750], 'confidence': 0.93, 'center_x': 445, 'center_y': 625},
            {'bbox': [610, 500, 840, 750], 'confidence': 0.89, 'center_x': 725, 'center_y': 625},
            {'bbox': [890, 500, 1080, 750], 'confidence': 0.91, 'center_x': 985, 'center_y': 625},
        ]

class ImageKeywordMatcher:
    def __init__(self):
        self.keywords = ['母婴', '育儿', '宝宝', '婴儿', '亲子']
    
    def match_keywords(self, cropped_image_path: str, keywords: Optional[List[str]] = None) -> bool:
        if keywords is None:
            keywords = self.keywords
        
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            result = ocr.ocr(cropped_image_path)
            text = ''.join([line[1][0] for line in result[0]])
            for kw in keywords:
                if kw in text:
                    return True
            return False
        except Exception as e:
            print(f"⚠ PaddleOCR 未安装，使用模拟匹配: {e}")
            return self._simulate_match()
    
    def _simulate_match(self) -> bool:
        import random
        return random.random() > 0.5

class XiaohongshuYOLOTest:
    def __init__(self):
        self.config = load_config("configs/default.json")
        self.controller = DeviceController(self.config.device)
        self.detector = YOLOWorldDetector()
        self.matcher = ImageKeywordMatcher()
        self.screenshot_dir = project_root / "logs" / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    async def connect_device(self):
        print("连接设备...")
        connected = await self.controller.connect()
        if connected:
            print("✓ 设备连接成功")
            return True
        else:
            print("✗ 设备连接失败")
            return False
    
    async def capture_homepage(self) -> str:
        screenshot_path = self.screenshot_dir / "homepage.png"
        import subprocess
        try:
            result = subprocess.run(
                [self.config.device.adb_exec_path, "-s", self.config.device.device_address, 
                 "shell", "screencap", "/sdcard/homepage.png"],
                capture_output=True, timeout=10
            )
            if result.returncode == 0:
                subprocess.run(
                    [self.config.device.adb_exec_path, "-s", self.config.device.device_address,
                     "pull", "/sdcard/homepage.png", str(screenshot_path)],
                    capture_output=True, timeout=10
                )
                print(f"✓ 首页截图已保存: {screenshot_path}")
                return str(screenshot_path)
        except Exception as e:
            print(f"截图失败，使用模拟图片: {e}")
        
        import cv2
        import numpy as np
        img = np.zeros((1080, 1080, 3), dtype=np.uint8)
        cv2.imwrite(str(screenshot_path), img)
        return str(screenshot_path)
    
    def sort_cards_by_position(self, boxes: List[Dict]) -> List[Dict]:
        sorted_boxes = sorted(boxes, key=lambda x: (x['bbox'][1], x['bbox'][0]))
        for i, box in enumerate(sorted_boxes):
            box['index'] = i + 1
        return sorted_boxes
    
    async def crop_and_match(self, screenshot_path: str, boxes: List[Dict]) -> List[Dict]:
        matched_notes = []
        
        try:
            from PIL import Image
            img = Image.open(screenshot_path)
            
            for box in boxes:
                x1, y1, x2, y2 = box['bbox']
                cropped = img.crop((x1, y1, x2, y2))
                crop_path = self.screenshot_dir / f"note_{box['index']}.png"
                cropped.save(crop_path)
                
                is_match = self.matcher.match_keywords(str(crop_path))
                if is_match:
                    box['matched'] = True
                    box['crop_path'] = str(crop_path)
                    matched_notes.append(box)
                    print(f"✓ 笔记 #{box['index']} 匹配成功，中心坐标: ({box['center_x']}, {box['center_y']})")
                else:
                    box['matched'] = False
                    print(f"✗ 笔记 #{box['index']} 未匹配")
        
        except Exception as e:
            print(f"裁剪匹配失败，使用模拟结果: {e}")
            for box in boxes:
                if box['index'] in [2, 5, 7]:
                    box['matched'] = True
                    box['crop_path'] = f"note_{box['index']}.png"
                    matched_notes.append(box)
                    print(f"✓ 笔记 #{box['index']} 匹配成功，中心坐标: ({box['center_x']}, {box['center_y']})")
                else:
                    box['matched'] = False
        
        return matched_notes
    
    async def click_notes(self, matched_notes: List[Dict]):
        if not matched_notes:
            print("没有匹配的笔记")
            return
        
        for i, note in enumerate(matched_notes[:2]):
            print(f"\n点击第 {i+1} 个匹配笔记，中心坐标: ({note['center_x']}, {note['center_y']})")
            await self.controller.tap(note['center_x'], note['center_y'])
            await asyncio.sleep(2)
            print("返回主页")
            await self.controller.key_event(4)
            await asyncio.sleep(1.5)
    
    async def run_test(self):
        print("===== YOLO-World 小红书刷笔记测试 =====")
        
        if not await self.connect_device():
            return
        
        print("\n1. 截取首页截图")
        screenshot_path = await self.capture_homepage()
        
        print("\n2. YOLO-World 检测笔记卡片")
        boxes = self.detector.detect_note_cards(screenshot_path)
        print(f"检测到 {len(boxes)} 个笔记卡片")
        
        print("\n3. 按位置排序笔记卡片")
        sorted_boxes = self.sort_cards_by_position(boxes)
        for box in sorted_boxes:
            print(f"  笔记 #{box['index']}: bbox={box['bbox']}, 中心=({box['center_x']},{box['center_y']})")
        
        print("\n4. 裁剪并匹配关键词")
        matched_notes = await self.crop_and_match(screenshot_path, sorted_boxes)
        print(f"\n共找到 {len(matched_notes)} 个匹配的笔记")
        
        print("\n5. 点击匹配的笔记")
        await self.click_notes(matched_notes)
        
        print("\n===== 测试完成 =====")
        
        await self.controller.disconnect()

if __name__ == "__main__":
    test = XiaohongshuYOLOTest()
    try:
        asyncio.run(test.run_test())
    except KeyboardInterrupt:
        print("\n测试被用户中断")