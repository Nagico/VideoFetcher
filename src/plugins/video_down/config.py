#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : config.py
# @Time     : 2021/9/5 8:39
# @Author   : NagisaCo
from pydantic import BaseSettings


class Config(BaseSettings):
    # 配置文件
    video_proxy: str = ""  # http代理(ip:port)
    video_config_file: str = ""  # 下载配置文件

    class Config:
        extra = "ignore"
