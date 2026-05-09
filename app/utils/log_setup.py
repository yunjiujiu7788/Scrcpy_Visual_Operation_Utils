"""Logging setup"""
from loguru import logger
import sys

def setup_logging(level="DEBUG"):
    logger.remove()
    logger.add(sys.stderr, level=level)
    logger.add("logs/app_{time:YYYY-MM-DD}.log", level="DEBUG")
    logger.add("logs/error_{time:YYYY-MM-DD}.log", level="ERROR")
    return logger
