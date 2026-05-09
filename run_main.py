import subprocess
import sys
import os

env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'

result = subprocess.run(
    [sys.executable, 'main.py', '--connect-only'],
    capture_output=True,
    text=True,
    cwd='D:\\pycharmobject\\Scrcpy 视觉操作通用工具',
    env=env
)

print('STDOUT:', result.stdout)
print('STDERR:', result.stderr)
print('Return code:', result.returncode)
