import os
from nonebot import get_driver

from .config import Config
from .data_source import Configer

global_config = get_driver().config
status_config = Config(**global_config.dict())  # 获取nonebot配置


configer = Configer(status_config.video_config_file)
