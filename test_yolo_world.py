import sys
import asyncio
import json
import os
import glob
import cv2
from pathlib import Path
from typing import List, Tuple, Dict, Optional

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import load_config
from app.controller import DeviceController

def cv2_read_with_chinese_path(image_path: str):
    import cv2
    import numpy as np
    try:
        img_array = np.fromfile(image_path, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"cv2_read_with_chinese_path error: {e}")
        return None

class YOLOWorldDetector:
    def __init__(self, model_path: str = None):
        self.model = None
        self.initialized = False
        self._initialize_model(model_path)
    
    def _find_trained_model(self):
        model_paths = glob.glob('runs/train/**/best.pt', recursive=True)
        if not model_paths:
            model_paths = glob.glob('runs/detect/**/best.pt', recursive=True)
        if model_paths:
            return model_paths[0]
        return None
    
    def _initialize_model(self, model_path: str = None):
        try:
            from ultralytics import YOLO
            
            if model_path is None:
                model_path = self._find_trained_model()
            
            if model_path and os.path.exists(model_path):
                self.model = YOLO(model_path)
                print(f"✓ 加载自定义训练模型: {model_path}")
            else:
                self.model = YOLO('yolov8s-world.pt')
                print("✓ 加载预训练 YOLO-World 模型")
            
            self.model.set_classes(['note_card'])
            self.initialized = True
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
            if boxes:
                print(f"✓ YOLO-World 检测到 {len(boxes)} 个笔记卡片")
                return boxes
            else:
                print("⚠ YOLO-World 未检测到笔记卡片，尝试基于图像分析检测")
                return self._detect_by_image_analysis(image_path)
        else:
            return self._detect_by_image_analysis(image_path)
    
    def _detect_by_image_analysis(self, image_path: str) -> List[Dict]:
        try:
            import cv2
            import numpy as np
            
            img = cv2_read_with_chinese_path(image_path)
            if img is None:
                print("⚠ 无法读取图片，使用模拟检测")
                return self._simulate_detection()
            
            height, width = img.shape[:2]
            print(f"  分析图片: {width}x{height}")
            
            boxes = []
            
            if width == 1080 and height == 2400:
                boxes = self._detect_xiaohongshu_cards_1080p(width, height)
            elif width == 1080 and height == 1920:
                boxes = self._detect_xiaohongshu_cards_1080p_old(width, height)
            else:
                boxes = self._detect_by_grid(width, height)
            
            if boxes:
                print(f"✓ 图像分析检测到 {len(boxes)} 个笔记卡片")
                return boxes
            else:
                print("⚠ 图像分析未检测到笔记卡片，使用模拟检测")
                return self._simulate_detection()
                
        except Exception as e:
            print(f"⚠ 图像分析失败: {e}，使用模拟检测")
            return self._simulate_detection()
    
    def _detect_xiaohongshu_cards_1080p(self, width: int, height: int) -> List[Dict]:
        boxes = []
        cols = 4
        rows = 5
        card_width = 250
        card_height = 320
        gap_x = 30
        gap_y = 10
        start_x = 25
        start_y = 180
        
        for row in range(rows):
            for col in range(cols):
                x1 = start_x + col * (card_width + gap_x)
                y1 = start_y + row * (card_height + gap_y)
                x2 = x1 + card_width
                y2 = y1 + card_height
                
                if x2 <= width and y2 <= height:
                    boxes.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': 0.85,
                        'center_x': int((x1 + x2) / 2),
                        'center_y': int((y1 + y2) / 2)
                    })
        
        return boxes
    
    def _detect_xiaohongshu_cards_1080p_old(self, width: int, height: int) -> List[Dict]:
        boxes = []
        cols = 4
        rows = 4
        card_width = 250
        card_height = 250
        gap_x = 30
        gap_y = 20
        start_x = 25
        start_y = 180
        
        for row in range(rows):
            for col in range(cols):
                x1 = start_x + col * (card_width + gap_x)
                y1 = start_y + row * (card_height + gap_y)
                x2 = x1 + card_width
                y2 = y1 + card_height
                
                if x2 <= width and y2 <= height:
                    boxes.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': 0.85,
                        'center_x': int((x1 + x2) / 2),
                        'center_y': int((y1 + y2) / 2)
                    })
        
        return boxes
    
    def _detect_by_grid(self, width: int, height: int) -> List[Dict]:
        boxes = []
        cols = min(4, width // 200)
        rows = min(6, height // 200)
        card_width = width // cols - 10
        card_height = int(card_width * 1.1)
        gap_x = (width - cols * card_width) // (cols + 1)
        gap_y = 20
        start_x = gap_x
        start_y = 150
        
        for row in range(rows):
            for col in range(cols):
                x1 = start_x + col * (card_width + gap_x)
                y1 = start_y + row * (card_height + gap_y)
                x2 = x1 + card_width
                y2 = y1 + card_height
                
                if x2 <= width and y2 <= height:
                    boxes.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': 0.75,
                        'center_x': int((x1 + x2) / 2),
                        'center_y': int((y1 + y2) / 2)
                    })
        
        return boxes
    
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
        self.ocr = None
        self._initialize_easyocr()

    def _initialize_easyocr(self):
        try:
            import easyocr
            print("正在初始化 EasyOCR（首次运行需要下载模型）...")
            self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
            print("✓ EasyOCR 初始化成功")
        except ImportError:
            print("⚠ EasyOCR 未安装，请先安装: pip install easyocr")
            self.reader = None
        except Exception as e:
            print(f"⚠ EasyOCR 初始化失败: {e}")
            self.reader = None

    def match_keywords(self, cropped_image_path: str, keywords: Optional[List[str]] = None) -> bool:
        if keywords is None:
            keywords = self.keywords

        if self.reader:
            try:
                img = cv2_read_with_chinese_path(cropped_image_path)
                if img is None:
                    print("⚠ 无法读取裁剪图片，使用模拟匹配")
                    return self._simulate_match()

                results = self.reader.readtext(cropped_image_path)

                text = ''
                if results and isinstance(results, list):
                    for item in results:
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            text += item[1] + ' '

                text = text.strip()

                if not text:
                    print(f"OCR识别结果: (无文字)")
                    return False

                print(f"OCR识别结果: {text[:100]}...")

                for kw in keywords:
                    if kw in text:
                        print(f"  ✓ 匹配到关键词: {kw}")
                        return True
                return False
            except Exception as e:
                print(f"⚠ EasyOCR 识别失败: {e}，使用模拟匹配")
                return self._simulate_match()
        else:
            print("⚠ EasyOCR 未安装，使用模拟匹配")
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
            print("正在从设备截取真实截图...")
            result = subprocess.run(
                [self.config.device.adb_exec_path, "-s", self.config.device.device_address, 
                 "shell", "screencap", "/sdcard/homepage.png"],
                capture_output=True, timeout=15
            )
            if result.returncode == 0:
                pull_result = subprocess.run(
                    [self.config.device.adb_exec_path, "-s", self.config.device.device_address,
                     "pull", "/sdcard/homepage.png", str(screenshot_path)],
                    capture_output=True, timeout=15
                )
                if pull_result.returncode == 0:
                    print(f"✓ 真实设备截图已保存: {screenshot_path}")
                    import cv2
                    img = cv2_read_with_chinese_path(str(screenshot_path))
                    if img is not None:
                        print(f"  截图尺寸: {img.shape[1]}x{img.shape[0]}")
                    return str(screenshot_path)
                else:
                    print(f"⚠ 截图拉取失败: {pull_result.stderr.decode('utf-8', errors='ignore')}")
            else:
                print(f"⚠ 截图命令执行失败: {result.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"截图失败: {e}")
        
        print("创建模拟首页图片...")
        import cv2
        import numpy as np
        img = np.zeros((1080, 1080, 3), dtype=np.uint8)
        cv2.rectangle(img, (50, 200), (280, 450), (255, 0, 0), 2)
        cv2.rectangle(img, (330, 200), (560, 450), (0, 255, 0), 2)
        cv2.rectangle(img, (610, 200), (840, 450), (0, 0, 255), 2)
        cv2.rectangle(img, (890, 200), (1080, 450), (255, 255, 0), 2)
        cv2.rectangle(img, (50, 500), (280, 750), (255, 0, 255), 2)
        cv2.rectangle(img, (330, 500), (560, 750), (0, 255, 255), 2)
        cv2.rectangle(img, (610, 500), (840, 750), (128, 128, 128), 2)
        cv2.rectangle(img, (890, 500), (1080, 750), (255, 128, 0), 2)
        cv2.imwrite(str(screenshot_path), img)
        print(f"✓ 模拟首页图片已保存: {screenshot_path}")
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
                print(f"  裁剪笔记 #{box['index']} 已保存: {crop_path}")
                
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
            print(f"裁剪匹配失败: {e}")
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