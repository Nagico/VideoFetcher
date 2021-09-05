#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : config.py
# @Time     : 2021/9/5 8:39
# @Author   : NagisaCo
from pydantic import BaseSettings


class Config(BaseSettings):
    # Your Config Here
    video_proxy: str = ""
    video_info_group: int = 0
    video_info_qq: int = 0
    video_bot_qq: int = 0

    class Config:
        extra = "ignore"