"""Config module"""
from pydantic import BaseModel, Field

class DeviceConfig(BaseModel):
    adb_exec_path: str = Field(default="adb")
    device_address: str = Field(default="127.0.0.1:5555")
    screenshot_quality: int = Field(default=30)
    screencap_method: str = Field(default="fast")
    input_method: str = Field(default="adb")

class Config(BaseModel):
    device: DeviceConfig
    targets: list = []
    tasks: list = []

def load_config(path):
    import json
    from pathlib import Path
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return Config(**raw)
