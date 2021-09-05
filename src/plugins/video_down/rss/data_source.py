#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : data_source.py
# @Time     : 2021/9/4 21:31
# @Author   : NagisaCo
import nonebot
import aiohttp
import asyncio
import sys
import feedparser
from typing import List
from nonebot.log import logger

getter = nonebot.plugin.require('src.plugins.video_down.getter')

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class YouRss(object):
    last_time = {}

    def __init__(self, channel_list: List, proxy=""):
        self.channel_list = channel_list
        self.proxy = proxy

    async def update(self):
        for channel_id in self.channel_list:
            result = await self._get_rss(channel_id)
            if len(result['entries']) == 0:
                continue
            last_time = YouRss.last_time.get(channel_id, None)
            YouRss.last_time[channel_id] = result['entries'][0]['updated_parsed']
            if last_time is not None:
                for video in result['entries']:
                    if video['updated_parsed'] <= last_time:
                        break
                    await self._download(video['link'])

    async def _download(self, url):
        logger.info(url)
        await getter.down_url(url)

    async def _get_rss(self, channel_id):
        url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'

        if self.proxy != "":
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), trust_env=True) as sess:
                async with sess.get(url=url, proxy=self.proxy) as res:
                    content = await res.read()
                    return feedparser.parse(content.decode(encoding='utf-8'))
        else:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url=url) as res:
                    content = await res.read()
                    return feedparser.parse(content.decode(encoding='utf-8'))

