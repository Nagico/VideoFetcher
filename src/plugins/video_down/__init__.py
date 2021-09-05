#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : __init__.py.py
# @Time     : 2021/9/4 22:50
# @Author   : NagisaCo
import nonebot
from .config import Config
from nonebot import get_driver

global_config = get_driver().config
status_config = Config(**global_config.dict())


export = nonebot.plugin.export()


@export
def check_proxy(url: str = "") -> str:
    if url == "":
        return status_config.video_proxy
    if status_config.video_proxy == "":
        return ""
    else:
        if 'youtube' in url:
            return status_config.video_proxy
        else:
            return ""


export.info_group = status_config.video_info_group
export.info_qq = status_config.video_info_qq
export.bot_qq = status_config.video_bot_qq


nonebot.plugin.load_plugin("src.plugins.video_down.getter")
nonebot.plugin.load_plugin("src.plugins.video_down.rss")
