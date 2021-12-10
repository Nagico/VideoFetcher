#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : config.py
# @Time     : 2021/9/1 15:01
# @Author   : NagisaCo
from pydantic import BaseSettings
from typing import Dict, Any


class Config(BaseSettings):
    # Your Config Here
    video_get_getter_status: Dict[int, Any] = {}
    video_get_getter_cnt: int = 0
    default_group_id: int = 0

    class Config:
        extra = "ignore"
