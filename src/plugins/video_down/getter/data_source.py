#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : data_source.py
# @Time     : 2021/9/1 15:03
# @Author   : NagisaCo
from __future__ import unicode_literals
from nonebot.log import logger
import youtube_dl
from youtube_dl.utils import UnavailableVideoError, MaxDownloadsReached
import asyncio
import functools
import os
import aiohttp
import aiofiles
import re


class YouGetter(object):
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
            # It also downloads the videos
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


class DownloadException(Exception):
    def __init__(self, Msg):
        self.Msg = Msg


if __name__ == "__main__":
    you = YouGetter('https://www.youtube.com/watch?v=GgRjQcZfxqQ')
    done = asyncio.run(you.get_info())

    print(done)
