#!/usr/bin/env python3
import sys
import os
import importlib.util

print('Testing import mechanism...', flush=True)

# 使用 importlib 来查看导入过程
try:
    # 查找模块规范
    spec = importlib.util.find_spec('app.config')
    print(f'Spec found: {spec}', flush=True)
    if spec:
        print(f'Origin: {spec.origin}', flush=True)
        print(f'Loader: {spec.loader}', flush=True)
        
except Exception as e:
    print(f'find_spec failed: {type(e).__name__}: {e}', flush=True)

print('\nTrying to import app first...', flush=True)
try:
    import app
    print(f'app module imported from: {app.__file__}', flush=True)
except Exception as e:
    print(f'Failed to import app: {type(e).__name__}: {e}', flush=True)
