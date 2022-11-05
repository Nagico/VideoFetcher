#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.onebot.v11 import Adapter

# Custom your logger
# 
# from nonebot.log import logger, default_format
# logger.add("error.log",
#            rotation="00:00",
#            diagnose=False,
#            level="ERROR",
#            format=default_format)

# You can pass some keyword args config to init function
nonebot.init()
nonebot.init(apscheduler_autostart=True)
nonebot.init(apscheduler_config={
    "apscheduler.timezone": "Asia/Shanghai"
})

app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)
# driver.register_adapter("mirai", MIRAIBot)

nonebot.load_plugin("src.plugins.video_down")

# Modify some config / config depends on loaded configs
# 
# config = driver.config
# do something...

nonebot.run()

