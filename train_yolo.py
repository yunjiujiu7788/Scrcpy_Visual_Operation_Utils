import argparse
import os
import sys
from ultralytics import YOLO
import torch

def get_device():
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        device_name = torch.cuda.get_device_name(0)
        print(f"✓ 检测到 GPU: {device_name}")
        return 0
    else:
        print("⚠ CUDA 不可用，使用 CPU 训练（速度较慢）")
        print("  如果需要 GPU 加速，请安装支持 CUDA 的 PyTorch 版本")
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"  当前 Python 版本: {python_version}")
        return 'cpu'

def train_model(data_yaml, epochs=100, batch=8, imgsz=1080, model='yolov8s-world.pt', resume=False):
    device = get_device()
    
    last_model_path = 'runs/detect/runs/train/xiaohongshu_notes/weights/last.pt'
    resume_path = last_model_path if (resume and os.path.exists(last_model_path)) else False
    
    if resume_path:
        print(f"\n===== 恢复训练 YOLO-World 模型 =====")
        print(f"从上次中断处继续训练: {resume_path}")
        model = YOLO(model)
        model.load(resume_path)
    else:
        print(f"\n===== 开始训练 YOLO-World 模型 =====")
        print(f"数据集配置: {data_yaml}")
        print(f"训练轮数: {epochs}")
        print(f"批次大小: {batch}")
        print(f"图像大小: {imgsz}")
        print(f"预训练模型: {model}")
        print(f"训练设备: {'GPU' if device != 'cpu' else 'CPU'}")
        model = YOLO(model)
    
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        workers=4,
        device=device,
        verbose=True,
        project='runs/train',
        name='xiaohongshu_notes',
        exist_ok=True,
        resume=False
    )
    
    print("\n===== 训练完成 =====")
    print(f"模型保存位置: runs/train/xiaohongshu_notes/weights/best.pt")
    
    return results

def validate_model(model_path, data_yaml):
    print(f"\n===== 开始验证模型 =====")
    model = YOLO(model_path)
    results = model.val(data=data_yaml)
    return results

def export_model(model_path, format='onnx'):
    print(f"\n===== 导出模型为 {format} 格式 =====")
    model = YOLO(model_path)
    model.export(format=format)
    print(f"模型已导出: {model_path.replace('.pt', f'.{format}')}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='训练小红书笔记卡片检测模型')
    parser.add_argument('--data', type=str, default='datasets/xiaohongshu/data.yaml', help='数据集配置文件')
    parser.add_argument('--epochs', type=int, default=100, help='训练轮数')
    parser.add_argument('--batch', type=int, default=8, help='批次大小')
    parser.add_argument('--imgsz', type=int, default=1080, help='输入图像大小')
    parser.add_argument('--model', type=str, default='yolov8s-world.pt', help='预训练模型')
    parser.add_argument('--validate', action='store_true', help='验证模型（不训练）')
    parser.add_argument('--export', type=str, default=None, help='导出格式（不训练）')
    parser.add_argument('--resume', action='store_true', help='从上次中断处恢复训练')
    parser.add_argument('--train', action='store_true', help='强制训练（与--validate/--export配合使用）')
    
    args = parser.parse_args()
    
    should_train = args.train or not (args.validate or args.export)
    
    if should_train:
        train_model(args.data, args.epochs, args.batch, args.imgsz, args.model, args.resume)
    
    model_path = 'runs/detect/runs/train/xiaohongshu_notes/weights/best.pt'
    
    if args.validate:
        validate_model(model_path, args.data)
    
    if args.export:
        export_model(model_path, args.export)