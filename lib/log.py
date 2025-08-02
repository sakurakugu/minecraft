from rich.logging import RichHandler
from rich.text import Text
import logging
import os
"""
这是一个 Python 脚本，用于设置日志输出。
上次编辑时间：2025年7月20日
作者：Sakurakugu
"""

class CustomRichHandler(RichHandler):
    LEVEL_NAME_MAP = {
        "CRITICAL": "[致命]",
        "ERROR": "[错误]",
        "WARNING": "[警告]",
        "INFO": "[信息]",
        "DEBUG": "[调试]",
        "NOTSET": "[未设置]",
    }
    
    LEVEL_COLOR_MAP = {
        "CRITICAL": "bold red",
        "ERROR": "red",
        "WARNING": "yellow",
        "INFO": "green",
        "DEBUG": "blue",
        "NOTSET": "dim",
    }

    def get_level_text(self, record):
        level_name = self.LEVEL_NAME_MAP.get(record.levelname, record.levelname)
        color = self.LEVEL_COLOR_MAP.get(record.levelname, "white")
        return Text(level_name, style=color)

# 全局变量存储日志文件名和目录
_log_path = './log/app.log'
_console_level = logging.DEBUG
_file_level = logging.DEBUG

def set_log_path(path):
    """
    设置日志路径，默认路径为 './log/app.log'。
    如果目录不存在，将自动创建。
    """
    global _log_path
    _log_path = path
    setup_logging()
    
def set_log_level(console_level, file_level=None):
    """
    设置日志级别
    - console_level: 控制台日志级别
    - file_level: 文件日志级别（可选，如果不设置则使用 console_level）
    有效值为：DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    global _console_level, _file_level
    _console_level = console_level
    if file_level is not None:
        _file_level = file_level
    setup_logging()

def setup_logging():
    """设置日志配置"""
    global _log_path
    
    # 确保日志目录存在
    if not os.path.exists(os.path.dirname(_log_path)):
        os.makedirs(os.path.dirname(_log_path), exist_ok=True)

    # 清除现有的处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建控制台处理器（带颜色）
    console_handler = CustomRichHandler()
    console_handler.setLevel(_console_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # 创建文件处理器（不带颜色）
    file_handler = logging.FileHandler(_log_path, encoding='utf-8')
    file_handler.setLevel(_file_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)-8s - %(lineno)-3d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # 配置日志
    # 根日志器设置为最低级别，确保所有日志都能传递到处理器
    root_logger.setLevel(min(_console_level, _file_level))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

# 初始化日志配置
setup_logging()

# 测试输出
# logging.debug("调试信息")
# logging.info("程序启动成功")
# logging.warning("注意：某个配置项缺失")
# logging.error("发生错误")
# logging.critical("系统崩溃")
