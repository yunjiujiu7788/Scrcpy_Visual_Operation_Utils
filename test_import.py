import sys
import importlib

print('Step 1: Starting', flush=True)

# 清除模块缓存
if 'app' in sys.modules:
    del sys.modules['app']
    print('Removed app from sys.modules', flush=True)
if 'app.config' in sys.modules:
    del sys.modules['app.config']
    print('Removed app.config from sys.modules', flush=True)

print('Step 2: Trying import with importlib...', flush=True)
try:
    spec = importlib.util.spec_from_file_location('app.config', 'app/config.py')
    print('Step 3: Got spec', flush=True)
    config_module = importlib.util.module_from_spec(spec)
    print('Step 4: Created module', flush=True)
    spec.loader.exec_module(config_module)
    print('Step 5: Import via importlib successful', flush=True)
    print(f'DeviceConfig: {config_module.DeviceConfig}', flush=True)
except Exception as e:
    print(f'Import failed: {type(e).__name__}: {e}', flush=True)

print('Step 6: Done', flush=True)
