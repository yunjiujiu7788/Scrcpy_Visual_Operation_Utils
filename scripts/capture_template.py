#!/usr/bin/env python3
"""
截图模板制作工具 — 从设备截图中截取小块作为模板
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import cv2
import numpy as np

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config import load_config, Config
from app.controller import DeviceController
from app.utils.screenshot import save_screenshot


class TemplateCapturer:
    """模板截取器"""

    def __init__(self, controller: DeviceController):
        self.controller = controller

    async def capture_full(self, save_path: str = "images/full_screen.png") -> str:
        """截取全屏并保存"""
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        img = await self.controller.screencap()
        cv2.imwrite(save_path, img)
        print(f"全屏截图已保存: {save_path}")
        print(f"  尺寸: {img.shape[1]}x{img.shape[0]}")
        return save_path

    async def interactive_crop(self, full_path: str, output_dir: str = "images"):
        """
        交互式裁剪 - 使用鼠标在图像上拖拽选择区域
        需要 OpenCV GUI 支持 (GUI 窗口)
        """
        img = cv2.imread(full_path)
        if img is None:
            print(f"无法读取图片: {full_path}")
            return

        print("\n=== 交互式模板截取 ===")
        print("1. 在弹出的窗口中用鼠标拖拽选择区域")
        print("2. 按 'c' 确认裁剪并保存")
        print("3. 按 'r' 重新选择")
        print("4. 按 ESC 退出")

        roi = cv2.selectROI("选择模板区域", img, showCrosshair=True)
        cv2.destroyAllWindows()

        if roi[2] == 0 or roi[3] == 0:
            print("未选择区域")
            return

        x, y, w, h = roi
        cropped = img[y : y + h, x : x + w]

        # 显示裁剪结果
        cv2.imshow("裁剪结果 (按 s 保存, 任意键取消)", cropped)
        key = cv2.waitKey(0) & 0xFF
        cv2.destroyAllWindows()

        if key == ord("s"):
            name = input("请输入模板文件名 (如 'button_confirm.png'): ").strip()
            if not name:
                name = f"template_{x}_{y}.png"
            if not name.endswith(".png"):
                name += ".png"
            save_path = os.path.join(output_dir, name)
            os.makedirs(output_dir, exist_ok=True)
            cv2.imwrite(save_path, cropped)
            print(f"模板已保存: {save_path}")
            print(f"  区域: ({x}, {y}, {w}, {h})")
            print(f"  尺寸: {w}x{h}")
        else:
            print("已取消保存")


async def main():
    parser = argparse.ArgumentParser(description="截图模板制作工具")
    parser.add_argument(
        "-c", "--config",
        default="configs/default.json",
        help="配置文件路径",
    )
    parser.add_argument(
        "-o", "--output",
        default="images/full_screen.png",
        help="全屏截图保存路径 (默认: images/full_screen.png)",
    )
    parser.add_argument(
        "--no-crop",
        action="store_true",
        help="截取全屏后退出，不进入交互裁剪模式",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    controller = DeviceController(config.device)

    try:
        print("正在连接设备...")
        await controller.connect()
        if not controller.is_connected:
            print("设备连接失败")
            return

        capturer = TemplateCapturer(controller)
        path = await capturer.capture_full(args.output)

        if not args.no_crop:
            await capturer.interactive_crop(path, "images")
        else:
            print("全屏截图完成")

    except KeyboardInterrupt:
        print("\n已取消")
    finally:
        await controller.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
