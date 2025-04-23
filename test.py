from loguru import logger
import sys

# 定义全局日志开关
GLOBAL_LOG_ENABLE = True

if GLOBAL_LOG_ENABLE:
    logger.enable("")
else:
    logger.disable("")

# 移除默认的日志处理器
logger.remove()
# 设置控制台日志级别
logger.add(sink=sys.stdout, level="INFO")

if __name__ == '__main__':
    # 示例日志记录
    logger.debug("这是一个调试日志")
    logger.info("这是一个信息日志")
    logger.warning("这是一个警告日志")
    logger.error("这是一个错误日志")
    logger.critical("这是一个严重错误日志")

    print("print-------------------------------------------")