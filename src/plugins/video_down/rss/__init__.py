#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : __init__.py.py
# @Time     : 2021/9/4 21:02
# @Author   : NagisaCo
import nonebot
from nonebot import require
from apscheduler.triggers.interval import IntervalTrigger
from .data_source import YouRss

scheduler = require("nonebot_plugin_apscheduler").scheduler


@scheduler.scheduled_job(IntervalTrigger(minutes=10))
async def update():
    you = YouRss(["UCXuqSBlHAE6Xw-yeJA0Tunw", "UCLxAS02eWvfZK4icRNzWD_g"], 'http://127.0.0.1:7890')
    await you.update()

