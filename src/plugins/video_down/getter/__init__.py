#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : __init__.py
# @Time     : 2021/9/1 15:00
# @Author   : NagisaCo
import os
import validators
import nonebot.exception
from nonebot import get_driver, on_command
from nonebot.typing import T_State
from nonebot.log import logger
from nonebot.adapters import Bot, Event

from .data_source import VideoGetter, DownEvent
from .config import Config
from ..exception import InfoException, DownloadException, UploadException

global_config = get_driver().config
status_config = Config(**global_config.dict())  # 获取nonebot配置

you_get = on_command("down", priority=3)  # 下载命令
get_status = on_command("down list", priority=2)  # 查看下载状态命令

status_config.video_get_getter_status = {}  # 初始化下载状态
status_config.video_get_getter_cnt = 0  # 初始化下载任务数量

export = nonebot.plugin.export()  # 导出插件
video_get = nonebot.plugin.require('src.plugins.video_down')  # 获取插件
configer = nonebot.plugin.require('src.plugins.video_down.configer').configer  # 获取配置插件


@you_get.handle()
async def handle_download(bot: Bot, event: Event, state: T_State):
    """
    处理下载任务
    """
    args = str(event.get_message()).strip()
    if args:
        state["url"] = args
        url = state["url"]
    else:
        await you_get.finish(f'please input "/down [url]"')
    result = validators.url(url)
    if result is not True:
        url = 'https://' + url  # 自动添加协议头
        result = validators.url(url)
        if result is not True:
            await you_get.finish(f'{url} is not a valid url')
    down_event = DownEvent(bot, event, state, configer)
    await down_video(down_event)
    pass


@export
async def down_video(down_event: DownEvent) -> None:
    await down_event.bot.send(down_event.event, f"got url\n{down_event.url}")

    down_event.proxy = video_get.check_proxy(down_event.url)
    down_event.you_getter = VideoGetter(down_event.url, down_event.proxy)

    @down_event.you_getter.register_callback
    def progress_call(data: dict):
        if data['status'] == 'downloading':
            try:
                down_event.details = f"{data['_percent_str']} of {data['_total_bytes_str']}" \
                                     f" at {data['_speed_str']} ETA {data['_eta_str']}"
                logger.info(f"{down_event.group_id}-{down_event.title}: {down_event.details}")
            except Exception as e:
                logger.error(f"{down_event.group_id}-{down_event.title} error: {e}")

        if data['status'] == 'finished':
            down_event.details = 'Download Finish'

    info = await down_event.you_getter.get_info()
    if info is None:
        raise InfoException("Invalid url, please input again")

    # Download
    down_event.title = info.get('title')
    await down_event.bot.send(down_event.event, f"start task\n{down_event.title}")
    try:
        await _download_video_task(down_event)
        await _download_cover_task(down_event)
    except DownloadException as e:
        await inform(down_event, e.msg)
        return

    # Upload
    try:
        await _upload_video_task(down_event)
        if down_event.cover_name != "":
            await _upload_cover_task(down_event)
    except UploadException as e:
        await inform(down_event, e.msg)
        return
    else:
        await down_event.bot.send(
            down_event.event,
            f"Title: {info['title']}\n"
            f"Platform: {info.get('extractor', '')}\n"
            f"Date: {info.get('upload_date', '')}\n"
            f"Author: {info.get('uploader', '').strip()}\n"
            f"\n"
            f"Url: {info.get('webpage_url', '')}\n"
            f"Video: {down_event.file_name}\n"
            f"Cover: {down_event.cover_name}\n"
            f"====================\n"
            f"[Description]\n"
            f"{info.get('description', '')}\n"
        )
        os.remove(down_event.file_name)
        if down_event.cover_name != "":
            os.remove(down_event.cover_name)
        await inform(down_event, 'success')
        return


async def _download_video_task(down_event: DownEvent) -> None:
    """
    下载视频子任务

    :param down_event: 下载事件
    """
    down_event.details = "downloading video"  # 设置下载状态
    try:
        down_event.file_name = await down_event.you_getter.download_video()  # 下载视频并返回文件名
    except DownloadException as e:  # 下载失败
        logger.error(f"{down_event.group_id}-{down_event.title} video-download error: {e}")
        raise DownloadException(f"Download failed\n\n{e}")  # 返回错误信息, 终止任务


async def _download_cover_task(down_event: DownEvent) -> None:
    """
    下载封面子任务

    :param down_event: 下载事件
    """
    down_event.details = "downloading cover"  # 设置下载状态
    try:
        down_event.cover_name = await down_event.you_getter.download_cover()  # 下载封面并返回文件名
    except DownloadException as e:  # 下载失败
        down_event.cover_name = ""  # 封面名称为空
        logger.error(f"{down_event.group_id}-{down_event.title} cover-download error: {e}")
        await down_event.bot.send(down_event.event, f"[{down_event.title}] Download cover failed\n\n{e}")  # 告知封面下载失败，继续任务


async def _upload_video_task(down_event: DownEvent) -> None:
    """
    上传视频子任务

    :param down_event: 下载事件
    """
    try:
        down_event.details = 'uploading video'
        folder_id = await down_event.get_folder_id(down_event.file_path)
        if folder_id == '':  # 根目录
            await down_event.bot.call_api(
                "upload_group_file",
                group_id=down_event.group_id,
                file=os.path.abspath(down_event.file_name),
                name=down_event.file_name)
        else:
            await down_event.bot.call_api(
                "upload_group_file",
                group_id=down_event.group_id,
                file=os.path.abspath(down_event.file_name),
                name=down_event.file_name,
                folder=folder_id)

    except nonebot.exception.FinishedException:
        raise nonebot.exception.FinishedException
    except nonebot.adapters.cqhttp.exception.ActionFailed as e:
        information = f"Upload failed.\n\n{e.info['wording']}"
        raise UploadException(information)
    except Exception as e:
        information = f"Upload failed.\n\n{e}"
        raise UploadException(information)


async def _upload_cover_task(down_event: DownEvent):
    """
    上传封面子任务

    :param down_event: 下载事件
    """
    try:
        if down_event.cover_name is not None:  # 封面存在
            down_event.details = 'uploading cover'
            folder_id = await down_event.get_folder_id(down_event.cover_path)

            if folder_id == '':  # 根目录
                await down_event.bot.call_api(
                    "upload_group_file",
                    group_id=down_event.group_id,
                    file=os.path.abspath(down_event.cover_name),
                    name=down_event.cover_name)
            else:
                await down_event.bot.call_api(
                    "upload_group_file",
                    group_id=down_event.group_id,
                    folder=folder_id,
                    file=os.path.abspath(down_event.cover_name),
                    name=down_event.cover_name)

    except nonebot.exception.FinishedException:
        raise nonebot.exception.FinishedException
    except nonebot.adapters.cqhttp.exception.ActionFailed as e:
        result = f"[{down_event.title}] Upload cover failed.\n\n{e.info['wording']}"
        logger.error(f"{down_event.group_id}-{down_event.title} upload cover error:{e.info['wording']}")
        await down_event.bot.send(down_event.event, result)
    except Exception as e:
        result = f"[{down_event.title}] Upload cover failed.\n\n{e}"
        logger.error(f"{down_event.group_id}-{down_event.title} upload cover error:{e}")
        await down_event.bot.send(down_event.event, result)


async def inform(down_event: DownEvent, result: str):
    """
    通知下载结果

    :param down_event: 下载事件
    :param result: 结果
    """
    await down_event.bot.call_api(
        'send_group_msg',
        group_id=down_event.group_id,
        message=f'[CQ:reply,id={down_event.message_id}]'
                f'[{down_event.title}] {result}\n'
                f'[CQ:at,qq={down_event.user_id}]'
    )
    del down_event
    await you_get.finish()


@get_status.handle()
async def handle_status(bot: Bot, event: Event, state: T_State):
    result = ""
    if event.message_type == 'group':
        for key, value in DownEvent.event_list.items():
            if value is not None and value.group_id == event.group_id:
                result += (f'[{value.title}]\n'
                           f'{value.details}\n\n')
    else:
        for key, value in status_config.video_get_getter_status.items():
            if value is not None:
                result += (f'[{value.group_id}-{value.title}]\n'
                           f'{value.details}\n\n')
    if result == "":
        await get_status.finish("no running task")
    else:
        await get_status.finish(result)
