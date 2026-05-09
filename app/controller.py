"""Device controller"""
from maa.controller import AdbController
from maa.toolkit import Toolkit
from maa.define import MaaAdbScreencapMethodEnum, MaaAdbInputMethodEnum
from app.config import DeviceConfig
import asyncio

class DeviceController:
    def __init__(self, config: DeviceConfig):
        self.config = config
        self._ctrl = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _get_screencap_method(self, method_str: str) -> int:
        method_map = {
            "fast": MaaAdbScreencapMethodEnum.Encode,
            "raw": MaaAdbScreencapMethodEnum.RawByNetcat,
            "minicap": MaaAdbScreencapMethodEnum.MinicapDirect,
        }
        return method_map.get(method_str.lower(), MaaAdbScreencapMethodEnum.Default)

    async def connect(self) -> bool:
        try:
            await asyncio.to_thread(Toolkit.init_option, "./")
            self._ctrl = AdbController(
                adb_path=self.config.adb_exec_path,
                address=self.config.device_address,
                screencap_methods=self._get_screencap_method(self.config.screencap_method),
                input_methods=MaaAdbInputMethodEnum.AdbShell,
            )
            connected = await asyncio.to_thread(self._ctrl.post_connection)
            if connected:
                self._connected = True
            return connected
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def disconnect(self):
        if self._ctrl:
            await asyncio.to_thread(self._ctrl.post_inactive)
            self._connected = False
            self._ctrl = None

    async def screencap(self):
        if not self._connected:
            raise Exception("Device not connected")
        return await asyncio.to_thread(self._ctrl.post_screencap)

    async def tap(self, x: int, y: int):
        if not self._connected:
            raise Exception("Device not connected")
        await asyncio.to_thread(self._ctrl.post_click(x, y).wait)

    async def swipe(self, start_x, start_y, end_x, end_y, duration_ms=300):
        if not self._connected:
            raise Exception("Device not connected")
        await asyncio.to_thread(self._ctrl.post_swipe(start_x, start_y, end_x, end_y, duration_ms).wait)

    async def input_text(self, text: str):
        if not self._connected:
            raise Exception("Device not connected")
        await asyncio.to_thread(self._ctrl.post_input_text(text).wait)

    async def key_event(self, keycode: int):
        if not self._connected:
            raise Exception("Device not connected")
        await asyncio.to_thread(self._ctrl.post_press_key(keycode).wait)