#!/usr/bin/env python3
"""
Complete test with all code in one file
"""
import sys
import os
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from maa.controller import AdbController
from maa.toolkit import Toolkit
from maa.define import MaaAdbScreencapMethodEnum, MaaAdbInputMethodEnum

print('Initializing...', flush=True)

# Config models
class DeviceConfig(BaseModel):
    adb_exec_path: str = Field(default="adb")
    device_address: str = Field(default="127.0.0.1:5555")
    screencap_method: str = Field(default="fast")
    input_method: str = Field(default="adb")

class DeviceController:
    def __init__(self, config: DeviceConfig):
        self.config = config
        self._ctrl = None
        self._connected = False

    def _get_screencap_method(self, method_str: str) -> int:
        method_map = {
            "fast": MaaAdbScreencapMethodEnum.Fast,
            "raw": MaaAdbScreencapMethodEnum.Raw,
            "minicap": MaaAdbScreencapMethodEnum.Minicap,
        }
        return method_map.get(method_str.lower(), MaaAdbScreencapMethodEnum.Default)

    async def connect(self) -> bool:
        print(f'Connecting to device: {self.config.device_address}', flush=True)
        try:
            await asyncio.to_thread(Toolkit.init_option, "./")
            self._ctrl = AdbController(
                adb_path=self.config.adb_exec_path,
                address=self.config.device_address,
                screencap_methods=self._get_screencap_method(self.config.screencap_method),
                input_methods=MaaAdbInputMethodEnum.Adb,
            )
            connected = await asyncio.to_thread(self._ctrl.post_connection)
            if connected:
                self._connected = True
                print(f'Device connected successfully!', flush=True)
            else:
                print('Device connection failed', flush=True)
            return connected
        except Exception as e:
            print(f'Connection error: {e}', flush=True)
            return False

async def main():
    print('Starting main...', flush=True)
    config = DeviceConfig()
    controller = DeviceController(config)
    
    try:
        await controller.connect()
    except Exception as e:
        print(f'Main error: {e}', flush=True)
    
    print('Done!', flush=True)

if __name__ == "__main__":
    asyncio.run(main())
