#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : data_source.py
# @Time     : 2021/9/1 15:03
# @Author   : NagisaCo
from __future__ import unicode_literals

from datetime import time

from nonebot import get_driver
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
import youtube_dl
from youtube_dl.utils import UnavailableVideoError, MaxDownloadsReached
import asyncio
import functools
import os
import aiohttp
import aiofiles
import re

from src.plugins.video_down.configer import Configer
from src.plugins.video_down.exception import DownloadException
from .config import Config

global_config = get_driver().config
status_config = Config(**global_config.dict())  # 获取nonebot配置


class VideoGetter(object):
    """
    视频下载器
    """
    def __init__(self, url: str, proxy: str = ""):
        self.ydl = None
        self.url = url
        self.callback = None
        self.proxy = proxy
        self.filename = ""
        self.covername = ""
        self.info = None

    def __del__(self):
        self.ydl.__exit__()

    class YouGetterLogger(object):
        """
        自定义日志类
        """
        @staticmethod
        def debug(msg):
            logger.info(msg)

        @staticmethod
        def warning(msg):
            logger.warning(msg)

        @staticmethod
        def error(msg):
            logger.error(msg)

    def register_callback(self, func):
        """
        注册回调函数
        """

        self.callback = func
        ydl_opts = {
            'format': 'bestvideo[height<=?1080][ext=mp4]+bestaudio[ext=m4a]/'
                      'bestvideo[height<=?1080][ext=mp4]+bestaudio/'
                      'best[height<=?1080]',
            'logger': self.YouGetterLogger(),
            'progress_hooks': [self.callback],
            'merge_output_format': 'mp4'
        }
        if self.proxy != "":
            ydl_opts.update({'you_get_proxy': self.proxy})
        self.ydl = youtube_dl.YoutubeDL(ydl_opts)
        self.ydl.__enter__()
        return func

    async def get_info(self):
        try:
            loop = asyncio.get_event_loop()
            self.info = await loop.run_in_executor(
                None,
                functools.partial(
                    self.ydl.extract_info,
                    self.url,
                    download=False
                )
            )
            self.filename = self.ydl.prepare_filename(self.info)
            self.covername = os.path.splitext(self.filename)[0]+os.path.splitext(re.sub(r'\?.*', '', self.info['thumbnail']))[-1]
            return self.info
        except UnavailableVideoError:
            self.ydl.report_error('unable to download video_down')
        except MaxDownloadsReached:
            self.ydl.to_screen('[info] Maximum number of downloaded files reached.')
        return None

    async def download_video(self) -> str:
        try:
            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                functools.partial(
                    self.ydl.extract_info,
                    self.url,
                    force_generic_extractor=self.ydl.params.get(
                        'force_generic_extractor',
                        False
                    )
                )
            )

            return self.filename
        except UnavailableVideoError:
            self.ydl.report_error('unable to download video_down')
            raise DownloadException('unable to download video_down')
        except MaxDownloadsReached:
            self.ydl.to_screen('[info] Maximum number of downloaded files reached.')
            raise DownloadException('[info] Maximum number of downloaded files reached.')
        except Exception as e:
            raise DownloadException(e)

    async def download_cover(self) -> str:
        try:
            cover_url = self.info['thumbnail']
            async with aiohttp.ClientSession() as session:
                if self.proxy != "":
                    img = await session.get(cover_url, proxy=self.proxy)
                else:
                    img = await session.get(cover_url)
                content = await img.read()
                async with aiofiles.open(self.covername, mode='wb') as f:
                    await f.write(content)
            return self.covername
        except Exception as e:
            raise DownloadException(e)


class DownEvent(object):
    """
    下载任务事件信息
    """
    event_list = {}
    event_cnt = 0

    def __init__(self, bot: Bot, event: Event, state: T_State, configer: Configer):
        DownEvent.event_cnt += 1
        self.id = DownEvent.event_cnt
        self.bot = bot
        self.event = event
        self.state = state
        self.configer = configer

        self.url = state['url']
        self.bot_qq = bot.self_id
        self.user_id = event.get_user_id()
        if event.message_type == 'group':
            self.group_id = event.group_id
        else:  # private
            self.group_id = status_config.default_group_id

        config_data = self.configer.get_config_data(self.group_id)
        self.group_name = config_data['group_name']
        self.message_id = event.message_id

        self.you_getter = None
        self.file_name = ''
        self.cover_name = ''
        self.title = ''
        self.details = 'init'

        self.file_path = config_data['video_upload_path']
        self.cover_path = config_data['cover_upload_path']

        self.create_time = time()
        self.finish_time = None

        DownEvent.event_list[self.id] = self  # 在列表中添加信息

    async def get_folder_id(self, path: str) -> str:
        if path == '':
            return ''

        if path[0] == '/':  # 处理/开头的路径
            path = path[1:]

        res = await self.bot.call_api('get_group_root_files', group_id=self.group_id)  # 获取根目录
        for folder in res['folders']:
            if folder['folder_name'] == path:  # 匹配目录名
                return folder['folder_id']  # 返回目录id

        return ''  # 未找到

    def destroy(self):
        DownEvent.event_list.pop(self.id)  # 在dict中删除信息
        if self.you_getter:
            del self.you_getter


if __name__ == "__main__":
    you = VideoGetter('https://www.youtube.com/watch?v=GgRjQcZfxqQ')
    done = asyncio.run(you.get_info())

    print(done)
