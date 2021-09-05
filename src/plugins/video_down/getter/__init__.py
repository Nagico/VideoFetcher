#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : __init__.py
# @Time     : 2021/9/1 15:00
# @Author   : NagisaCo
import nonebot.exception
from nonebot import get_driver, on_command
from nonebot.typing import T_State
from nonebot.log import logger
from nonebot.adapters import Bot, Event
from .data_source import YouGetter
from .config import Config
import os

global_config = get_driver().config
status_config = Config(**global_config.dict())

you_get = on_command("down", priority=3)
get_status = on_command("down status", priority=2)

status_config.video_get_getter_status = {}

export = nonebot.plugin.export()
video_get = nonebot.plugin.require('src.plugins.video_down')


@you_get.handle()
async def handle_first_receive(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["url"] = args


@you_get.got("url", prompt="Input your url")
async def handle_url(bot: Bot, event: Event, state: T_State):
    url = state["url"]
    try:
        await down_url(url, bot, event)
    except InfoException as e:
        await you_get.reject(e.Msg)


@export
async def down_url(url: str, bot: Bot = None, event: Event = None) -> None:
    Mode = 0  # 提交模式

    if bot is None and event is None:
        Mode = 1  # 自动更新模式
        try:
            bot = nonebot.get_bot(str(video_get.bot_qq))
        except Exception:
            bot = nonebot.get_bot()

        event = nonebot.adapters.cqhttp.Event(
            anonymous=None,
            font=0,
            group_id=video_get.info_group,
            message_id=0,
            message_seq=0,
            message_type='group',
            post_type='message',
            raw_message="",
            self_id=bot.self_id,
            sub_type='normal',
            time=1,
            to_me=True,
            user_id=video_get.info_qq
        )

    if Mode == 0:
        await bot.send(event, f"Got url\n{url}")

    proxy = video_get.check_proxy(url)
    you_getter = YouGetter(url, proxy)

    @you_getter.register_callback
    def progress_call(data: dict):
        if data['status'] == 'downloading':
            try:
                status_config.video_get_getter_status[title] = (
                    f"{data['_percent_str']} of {data['_total_bytes_str']} "
                    f"at {data['_speed_str']} ETA {data['_eta_str']}")
                logger.info(f"{title}: {status_config.video_get_getter_status[info.get('title')]}")
            except Exception:
                pass
        if data['status'] == 'finished':
            status_config.video_get_getter_status[info.get('title')] = 'Download Finish'

    info = await you_getter.get_info()
    if info is None:
        raise InfoException("Invalid url, please input again")

    # Download
    title = info.get('title')
    if Mode == 0:
        await bot.send(event, f"[{title}] Start downloading")
    try:
        filename = await _download_video(title, you_getter)
        covername = await _download_cover(bot, event, title, you_getter)
    except DownloadException as e:
        await _clean(you_getter, bot, event, title, e.Msg, Mode)
        return

    # Upload
    if Mode == 0:
        await bot.send(event, f"[{title}] Start uploading")
    try:
        await _upload_video(bot, title, filename)
        if covername != "":
            await _upload_cover(bot, event, title, covername)
    except UploadException as e:
        await _clean(you_getter, bot, event, title, e.Msg, Mode)
        return
    else:
        await bot.send(
            event,
            f"Title: {info['title']}\n"
            f"Platform: {info.get('extractor', '')}\n"
            f"Date: {info.get('upload_date', '')}\n"
            f"Author: {info.get('uploader', '').strip()}\n"
            f"\n"
            f"Url: {info.get('webpage_url', '')}\n"
            f"Video: {filename}\n"
            f"Cover: {covername}\n"
            f"====================\n"
            f"[Description]\n"
            f"{info.get('description', '')}\n"
        )
        os.remove(filename)
        if covername != "":
            os.remove(covername)
        await _clean(you_getter, bot, event, title, 'Success', Mode)
        return


async def _download_video(title: str, you_getter: YouGetter) -> str:
    status_config.video_get_getter_status[title] = "Downloading video_down"
    try:
        filename = await you_getter.download_video()
    except data_source.DownloadException as e:
        raise DownloadException(f"Download failed\n\n"
                                f"{e}")
    return filename


async def _download_cover(bot: Bot, event: Event, title: str, you_getter: YouGetter) -> str:
    status_config.video_get_getter_status[title] = "Downloading cover"
    try:
        covername = await you_getter.download_cover()
    except data_source.DownloadException as e:
        covername = ""
        await bot.send(
            event,
            f"[{title}] Download cover failed\n\n"
            f"{e}")
    return covername


async def _upload_video(bot: Bot, title: str, filename: str) -> None:
    try:
        status_config.video_get_getter_status[title] = 'Uploading video_down'
        await bot.call_api(
            "upload_group_file",
            group_id="549116573",
            file=os.path.abspath(filename),
            name=filename)
    except nonebot.exception.FinishedException:
        raise nonebot.exception.FinishedException
    except nonebot.adapters.cqhttp.exception.ActionFailed as e:
        information = f"Upload failed.\n\n" \
                      f"{e.info['wording']}"
        raise UploadException(information)
    except Exception as e:
        information = f"Upload failed.\n\n" \
                      f"{e}"
        raise UploadException(information)


async def _upload_cover(bot: Bot, event: Event, title: str, covername: str):
    try:
        if covername is not None:
            status_config.video_get_getter_status[title] = 'Uploading cover'
            await bot.call_api(
                "upload_group_file",
                group_id="549116573",
                file=os.path.abspath(covername),
                name=covername)
    except nonebot.exception.FinishedException:
        raise nonebot.exception.FinishedException
    except nonebot.adapters.cqhttp.exception.ActionFailed as e:
        result = f"[{title}] Upload cover failed.\n\n" \
                 f"{e.info['wording']}"
        await bot.send(event, result)
    except Exception as e:
        result = f"[{title}] Upload cover failed.\n\n" \
                 f"{e}"
        await bot.send(event, result)


async def _clean(you_getter: YouGetter, bot: Bot, event: Event, title: str, result: str, Mode: int):
    del status_config.video_get_getter_status[title]
    del you_getter
    if event.message_type == 'group':
        await bot.call_api(
            'send_group_msg',
            group_id=event.group_id,
            message=f'[CQ:reply,id={event.message_id}]'
                    f'[{title}] {result}\n'
                    f'[CQ:at,qq={event.user_id}]'
        )
        if Mode == 0:
            await you_get.finish()
    elif event.message_type == "private":
        await bot.call_api(
            'send_private_msg',
            user_id=event.user_id,
            message=f'[CQ:reply,id={event.message_id}]'
                    f'[{title}] {result}\n'
                    f'[CQ:shake]'
        )
        if Mode == 0:
            await you_get.finish()
    else:
        if Mode == 0:
            await you_get.finish(f'[{title}] {result}')


class UploadException(Exception):
    def __init__(self, Msg):
        self.Msg = Msg


class DownloadException(Exception):
    def __init__(self, Msg):
        self.Msg = Msg


class InfoException(Exception):
    def __init__(self, Msg):
        self.Msg = Msg


@get_status.handle()
async def handle_status(bot: Bot, event: Event, state: T_State):
    result = ""
    for item in status_config.video_get_getter_status:
        if status_config.video_get_getter_status[item] is not None:
            result += (f'[{item}]\n'
                       f'{status_config.video_get_getter_status[item]}\n\n')
    if result == "":
        await get_status.finish("No running task")
    else:
        await get_status.finish(result)
