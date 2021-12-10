#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : config.py
# @Time     : 2021/9/4 21:24
# @Author   : NagisaCo
from pydantic import BaseSettings
from typing import List


class Config(BaseSettings):
    # Your Config Here

    class Config:
        extra = "ignore"