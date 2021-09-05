#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : __init__.py.py
# @Time     : 2021/9/4 21:02
# @Author   : NagisaCo
import nonebot
from nonebot import require, get_driver
from apscheduler.triggers.interval import IntervalTrigger
from .data_source import YouRss
from .config import Config

global_config = get_driver().config
status_config = Config(**global_config.dict())


scheduler = require("nonebot_plugin_apscheduler").scheduler
video_get = nonebot.plugin.require('src.plugins.video_down')


@scheduler.scheduled_job(IntervalTrigger(minutes=10))
async def update():
    you = YouRss(status_config.you_rss_channel_list, video_get.check_proxy())
    await you.update()

