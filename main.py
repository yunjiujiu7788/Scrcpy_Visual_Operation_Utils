#!/usr/bin/env python3
"""
Scrcpy 视觉操作通用工具 — 主入口
基于 MaaFramework + OpenCV + PaddleOCR 的手机视觉自动化框架
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# 将项目根目录加入 Python 路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config import load_config
from app.controller import DeviceController
from app.executor import TaskExecutor
from app.utils.log_setup import setup_logging


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Scrcpy 视觉操作通用工具 — 基于 MaaFramework 的手机视觉自动化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用默认配置运行
  python main.py

  # 指定配置文件
  python main.py -c configs/my_task.json

  # 只连接设备，不执行任务
  python main.py --connect-only

  # 执行指定任务
  python main.py -t "每日签到"

  # 日志级别
  python main.py --log-level DEBUG
        """,
    )

    parser.add_argument(
        "-c", "--config",
        default="configs/default.json",
        help="配置文件路径 (默认: configs/default.json)",
    )
    parser.add_argument(
        "-t", "--task",
        default=None,
        help="要执行的任务名称（不指定则执行所有 manual 和 on_start 任务）",
    )
    parser.add_argument(
        "--connect-only",
        action="store_true",
        help="仅连接设备，不执行任务（用于测试连接）",
    )
    parser.add_argument(
        "--log-level",
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: DEBUG)",
    )
    parser.add_argument(
        "--images-dir",
        default="images",
        help="模板图片所在目录 (默认: images)",
    )

    return parser.parse_args()


async def main():
    """主入口"""
    args = parse_args()

    # 加载 .env 环境变量
    load_dotenv()

    # 初始化日志
    setup_logging(level=args.log_level)

    # 加载配置文件
    config_path = Path(project_root) / args.config
    if not config_path.exists():
        # 尝试相对路径
        config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"配置文件不存在: {args.config}")
        sys.exit(1)

    try:
        config = load_config(config_path)
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        sys.exit(1)

    # 初始化设备控制器
    controller = DeviceController(config.device)
    executor = TaskExecutor(config, images_dir=args.images_dir)

    try:
        # 连接设备
        logger.info(f"正在连接设备: {config.device.device_address}")
        connected = await controller.connect()

        if not connected:
            logger.error("设备连接失败，请检查 ADB 连接状态")
            logger.info("提示: 确保 scrcpy / adb 已连接，尝试: adb connect 127.0.0.1:5555")
            sys.exit(1)

        logger.info("设备连接成功")
        executor.set_controller(controller)

        if args.connect_only:
            logger.info("连接测试完成（--connect-only 模式）")
            return

        # 执行任务
        if args.task:
            # 执行指定任务
            logger.info(f"执行指定任务: {args.task}")
            success = await executor.execute_task(args.task)
            if not success:
                logger.warning(f"任务 '{args.task}' 执行不完全成功")
        else:
            # 执行所有 on_start 和 manual 任务
            logger.info("执行启动任务和手动任务...")
            results = await executor.execute_tasks_with_trigger("on_start")
            on_start_results = await executor.execute_tasks_with_trigger("manual")
            all_results = results + on_start_results

            success_count = sum(1 for _, ok in all_results if ok)
            total_count = len(all_results)
            logger.info(f"任务执行完成: {success_count}/{total_count} 成功")

            for task_name, ok in all_results:
                status = "✓" if ok else "✗"
                logger.info(f"  [{status}] {task_name}")

    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在退出...")
    except Exception as e:
        logger.exception(f"运行异常: {e}")
    finally:
        # 断开连接
        if controller.is_connected:
            await controller.disconnect()
            logger.info("设备已断开连接")


if __name__ == "__main__":
    asyncio.run(main())
