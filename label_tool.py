import os
import cv2
import numpy as np
import shutil
from pathlib import Path

# 配置
RAW_DIR = Path('raw_screenshots')
OUTPUT_IMG_DIR = Path('datasets/xiaohongshu/images/train')
OUTPUT_LABEL_DIR = Path('datasets/xiaohongshu/labels/train')

# 创建目录
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_LABEL_DIR.mkdir(parents=True, exist_ok=True)

def get_image_list():
    """获取待标注图片列表"""
    exts = ['.jpg', '.jpeg', '.png', '.bmp']
    return [f.name for f in RAW_DIR.iterdir() if f.suffix.lower() in exts]

def convert_to_yolo(img_path, boxes):
    """将像素坐标转换为YOLO格式"""
    img = cv2.imread(str(img_path))
    if img is None:
        return None
    img_height, img_width = img.shape[:2]
    
    yolo_lines = []
    for box in boxes:
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) / 2 / img_width
        center_y = (y1 + y2) / 2 / img_height
        width = abs(x2 - x1) / img_width
        height = abs(y2 - y1) / img_height
        
        # 确保在有效范围内
        center_x = max(0.001, min(0.999, center_x))
        center_y = max(0.001, min(0.999, center_y))
        width = max(0.001, min(0.999, width))
        height = max(0.001, min(0.999, height))
        
        yolo_lines.append(f'0 {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}')
    return yolo_lines

def main():
    images = get_image_list()
    if not images:
        print('❌ 未找到待标注图片，请将图片放入 raw_screenshots 目录')
        return
    
    print(f'📁 找到 {len(images)} 张待标注图片')
    
    for idx, filename in enumerate(images):
        img_path = RAW_DIR / filename
        img = cv2.imread(str(img_path))
        if img is None:
            print(f'❌ 无法读取图片: {filename}')
            continue
        
        print(f'\n📝 正在标注第 {idx+1}/{len(images)} 张: {filename}')
        print('操作说明:')
        print('  - 鼠标左键点击两次创建矩形框')
        print('  - 按 Z 键撤销最后一个框')
        print('  - 按 R 键重置当前图片')
        print('  - 按 S 键保存并进入下一张')
        print('  - 按 D 键跳过当前图片')
        print('  - 按 ESC 退出程序')
        
        boxes = []
        points = []
        temp_box = None
        
        def draw(img_copy):
            for box in boxes:
                x1, y1, x2, y2 = box
                cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            if temp_box:
                x1, y1, x2, y2 = temp_box
                cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 255, 255), 2)
            
            for i, (x, y) in enumerate(points):
                cv2.circle(img_copy, (x, y), 5, (0, 0, 255), -1)
                cv2.putText(img_copy, str(i+1), (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            cv2.putText(img_copy, f'已标注: {len(boxes)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            return img_copy
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal points, temp_box
            
            if event == cv2.EVENT_LBUTTONDOWN:
                if len(points) == 0:
                    points.append((x, y))
                elif len(points) == 1:
                    points.append((x, y))
                    x1, y1 = points[0]
                    x2, y2 = points[1]
                    box = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                    boxes.append(box)
                    points = []
                    temp_box = None
            elif event == cv2.EVENT_MOUSEMOVE and len(points) == 1:
                x1, y1 = points[0]
                temp_box = (x1, y1, x, y)
        
        cv2.namedWindow('标注工具', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('标注工具', 960, 720)
        cv2.setMouseCallback('标注工具', mouse_callback)
        
        while True:
            img_copy = img.copy()
            img_copy = draw(img_copy)
            cv2.imshow('标注工具', img_copy)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('z') or key == ord('Z'):
                if boxes:
                    boxes.pop()
                    print(f'已撤销，当前框数: {len(boxes)}')
            
            elif key == ord('r') or key == ord('R'):
                boxes = []
                points = []
                temp_box = None
                print('已重置')
            
            elif key == ord('s') or key == ord('S'):
                if len(boxes) == 0:
                    print('⚠ 未标注任何框，跳过保存')
                    break
                
                # 复制图片
                count = len(list(OUTPUT_IMG_DIR.glob('*.jpg'))) + 1
                ext = filename.split('.')[-1]
                new_name = f'{count:04d}.{ext}'
                shutil.copy(str(img_path), str(OUTPUT_IMG_DIR / new_name))
                
                # 保存标签
                yolo_lines = convert_to_yolo(img_path, boxes)
                label_path = OUTPUT_LABEL_DIR / f'{new_name.replace(f".{ext}", ".txt")}'
                with open(label_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(yolo_lines))
                
                print(f'✅ 已保存 {len(boxes)} 个标注框')
                cv2.destroyWindow('标注工具')
                break
            
            elif key == ord('d') or key == ord('D'):
                print('⏭️ 跳过当前图片')
                cv2.destroyWindow('标注工具')
                break
            
            elif key == 27:  # ESC
                print('🚪 退出程序')
                cv2.destroyAllWindows()
                return
    
    cv2.destroyAllWindows()
    print('\n🎉 标注完成!')

if __name__ == '__main__':
    main()