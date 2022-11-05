#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : __init__.py.py
# @Time     : 2021/9/4 22:50
# @Author   : NagisaCo
import nonebot

# nonebot.load_plugin("src.plugins.video_down.configer")
# nonebot.load_plugin("src.plugins.video_down.getter")

from .config import Config
from nonebot import get_driver, require

require("src.plugins.video_down.configer")
require("src.plugins.video_down.getter")

global_config = get_driver().config
status_config = Config(**global_config.dict())


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

