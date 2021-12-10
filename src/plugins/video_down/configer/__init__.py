import os
from nonebot import get_driver, plugin

from .config import Config
from .data_source import Configer

global_config = get_driver().config
status_config = Config(**global_config.dict())  # 获取nonebot配置

export = plugin.export()  # 导出插件

configer = Configer(status_config.video_config_file)

export.configer = configer
