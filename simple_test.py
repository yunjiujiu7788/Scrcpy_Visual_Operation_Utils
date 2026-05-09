#!/usr/bin/env python3
"""
Simple test script to verify basic functionality
"""
import sys

print('Python version:', sys.version)
print('Python path:', sys.path[:3])

# Test maa import
print('\nTesting maa import...')
try:
    import maa
    print('maa imported successfully')
    print('maa modules:', dir(maa)[:10])
except Exception as e:
    print(f'Failed to import maa: {e}')

# Test pydantic
print('\nTesting pydantic import...')
try:
    from pydantic import BaseModel
    print('pydantic imported successfully')
except Exception as e:
    print(f'Failed to import pydantic: {e}')

# Test opencv
print('\nTesting opencv import...')
try:
    import cv2
    print('opencv imported successfully')
except Exception as e:
    print(f'Failed to import opencv: {e}')

print('\nAll tests completed!')
