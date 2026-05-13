import os
import glob

def fix_label_file(label_path):
    fixed_lines = []
    has_error = False
    
    with open(label_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split()
        if len(parts) != 5:
            has_error = True
            continue
        
        cls = int(parts[0])
        x_center = float(parts[1])
        y_center = float(parts[2])
        width = float(parts[3])
        height = float(parts[4])
        
        x_center = max(0.0001, min(0.9999, x_center))
        y_center = max(0.0001, min(0.9999, y_center))
        width = max(0.0001, min(0.9999, width))
        height = max(0.0001, min(0.9999, height))
        
        x_min = x_center - width / 2
        x_max = x_center + width / 2
        y_min = y_center - height / 2
        y_max = y_center + height / 2
        
        if x_min < 0:
            width = width + x_min * 2
            x_center = x_center + x_min
            x_center = max(0.0001, x_center)
        
        if x_max > 1:
            width = width - (x_max - 1) * 2
            x_center = x_center - (x_max - 1)
            x_center = min(0.9999, x_center)
        
        if y_min < 0:
            height = height + y_min * 2
            y_center = y_center + y_min
            y_center = max(0.0001, y_center)
        
        if y_max > 1:
            height = height - (y_max - 1) * 2
            y_center = y_center - (y_max - 1)
            y_center = min(0.9999, y_center)
        
        width = max(0.0001, min(0.9999, width))
        height = max(0.0001, min(0.9999, height))
        
        fixed_lines.append(f"{cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    
    with open(label_path, 'w') as f:
        for line in fixed_lines:
            f.write(line + '\n')
    
    return has_error, len(fixed_lines)

def fix_all_labels(labels_dir):
    label_files = glob.glob(os.path.join(labels_dir, '*.txt'))
    total_files = len(label_files)
    fixed_files = 0
    total_boxes = 0
    
    print(f"正在修复 {labels_dir} 目录下的标注文件...")
    
    for label_path in label_files:
        has_error, box_count = fix_label_file(label_path)
        if has_error:
            fixed_files += 1
        total_boxes += box_count
        print(f"  修复: {os.path.basename(label_path)} ({box_count} 个框)")
    
    print(f"\n修复完成:")
    print(f"  总文件数: {total_files}")
    print(f"  修复文件数: {fixed_files}")
    print(f"  总边界框数: {total_boxes}")

if __name__ == '__main__':
    print("===== 标注文件修复工具 =====")
    
    train_labels_dir = 'datasets/xiaohongshu/labels/train'
    val_labels_dir = 'datasets/xiaohongshu/labels/val'
    
    fix_all_labels(train_labels_dir)
    print()
    fix_all_labels(val_labels_dir)
    
    print("\n✅ 所有标注文件已修复！")