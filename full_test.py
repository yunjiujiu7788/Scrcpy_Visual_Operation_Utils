import sys
import os

# 设置项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 删除所有缓存
for root, dirs, files in os.walk(project_root):
    for d in dirs:
        if d == '__pycache__':
            import shutil
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)

print('Cache cleaned', flush=True)

# 现在尝试导入
try:
    from app.config import load_config
    print('Import successful!', flush=True)
except Exception as e:
    print(f'Import failed: {type(e).__name__}: {e}', flush=True)
    import traceback
    traceback.print_exc()
