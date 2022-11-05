import json
import os
from nonebot import get_driver, plugin, on_command
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event, Message
from nonebot.permission import SUPERUSER

from .config import Config
from .data_source import Configer

global_config = get_driver().config
status_config = Config(**global_config.dict())  # 获取nonebot配置

configer = Configer(status_config.video_config_file)

configer_add = on_command("configer add", permission=SUPERUSER, priority=2)
configer_delete = on_command("configer delete", permission=SUPERUSER, priority=2)
configer_list = on_command("configer list", permission=SUPERUSER, priority=2)
configer_get = on_command("configer get", permission=SUPERUSER, priority=2)
configer_update = on_command("configer update", permission=SUPERUSER, priority=2)
configer_help = on_command("configer help", permission=SUPERUSER, priority=2)


@configer_add.handle()
async def handle_configer_add(matcher: Matcher, args: Message = CommandArg()):
    args = str(args.extract_plain_text()).strip()  # 首次发送命令时跟随的参数 群号
    if args:
        matcher.set_arg("group_id", args)


@configer_add.got("group_id", prompt="请输入要添加的群号")
async def got_add_group_id(state: T_State, msg: Message = CommandArg()):
    if type(eval(msg.extract_plain_text().strip())) != int:
        await configer_add.reject('请输入正确的群号')
    state["group_id"] = int(msg.extract_plain_text().strip())


@configer_add.got("group_name", prompt="请输入群名")
async def got_add_group_name(state: T_State, msg: Message = CommandArg()):
    state["group_name"] = msg.extract_plain_text().strip()


@configer_add.got("video_upload_path", prompt="请输入视频上传路径, / 代表根目录")
async def got_add_video_upload_path(state: T_State, msg: Message = CommandArg()):
    state["video_upload_path"] = msg.extract_plain_text().strip()


@configer_add.got("cover_upload_path", prompt="请输入封面上传路径, / 代表根目录")
async def got_add_cover_upload_path(state: T_State, msg: Message = CommandArg()):
    state["cover_upload_path"] = msg.extract_plain_text().strip()


@configer_add.got("enable_subscribe", prompt="请输入是否开启订阅,True or False")
async def got_add_enable_subscribe(state: T_State, msg: Message = CommandArg()):
    state["enable_subscribe"] = True if msg.extract_plain_text().strip().lower() == 'true' else False

    await configer_add.send(f'当前添加的配置为:\n'
                            f'群号: {state["group_id"]}\n'
                            f'群名: {state["group_name"]}\n'
                            f'视频上传路径: {state["video_upload_path"]}\n'
                            f'封面上传路径: {state["cover_upload_path"]}\n'
                            f'是否开启订阅: {state["enable_subscribe"]}\n')


@configer_add.got("confirm", prompt="请输入是否确认添加,True or False")
async def got_add_confirm(state: T_State, msg: Message = CommandArg()):
    state["confirm"] = True if msg.extract_plain_text().strip().lower() == 'true' else False

    if not state["confirm"]:
        await configer_add.finish('已取消')

    await configer.set_config_data(group_id=state["group_id"], group_name=state["group_name"],
                                   video_upload_path=state["video_upload_path"],
                                   cover_upload_path=state["cover_upload_path"],
                                   enable_subscribe=state["enable_subscribe"])

    await configer_add.finish('添加成功')


@configer_delete.handle()
async def handle_configer_delete(state: T_State, msg: Message = CommandArg()):
    args = msg.extract_plain_text().strip()  # 首次发送命令时跟随的参数 群号
    if args:
        state["group_id"] = args  # 如果用户发送了参数则直接赋值


@configer_delete.got("group_id", prompt="请输入要删除的群号")
async def got_delete_group_id(state: T_State, msg: Message = CommandArg()):
    if type(eval(msg.extract_plain_text().strip())) != int:
        await configer_delete.reject('请输入正确的群号')
    state["group_id"] = int(msg.extract_plain_text().strip())

    if not configer.get_group_status(state["group_id"]):
        await configer_delete.finish('群号配置不存在, 已退出删除')

    configer_data = configer.get_config_data(state["group_id"])
    await configer_delete.send(f'当前删除的配置为:\n'
                               f'群号: {configer_data["group_id"]}\n'
                               f'群名: {configer_data["group_name"]}\n'
                               f'视频上传路径: {configer_data["video_upload_path"]}\n'
                               f'封面上传路径: {configer_data["cover_upload_path"]}\n'
                               f'是否开启订阅: {configer_data["enable_subscribe"]}\n'
                               f'订阅列表: {configer_data["subscribe_channel"]}')


@configer_delete.got("confirm", prompt="请输入是否确认删除,True or False")
async def got_delete_confirm(state: T_State, msg: Message = CommandArg()):
    state["confirm"] = True if msg.extract_plain_text().strip().lower() == 'true' else False

    if not state["confirm"]:
        await configer_delete.finish('已取消')

    await configer.delete_config_data(state["group_id"])

    await configer_delete.finish('删除成功')


@configer_list.handle()
async def handle_configer_list():
    config_data = configer.get_config_data()
    await configer_list.finish(json.dumps(config_data, ensure_ascii=False, indent=4))


@configer_update.handle()
async def handle_configer_update(state: T_State, msg: Message = CommandArg()):
    args = msg.extract_plain_text().strip()  # 首次发送命令时跟随的参数 群号
    if args:
        state["group_id"] = args  # 如果用户发送了参数则直接赋值


@configer_update.got("group_id", prompt="请输入要更新的群号")
async def got_add_group_id(state: T_State, msg: Message = CommandArg()):
    if type(eval(msg.extract_plain_text().strip())) != int:
        await configer_update.reject('请输入正确的群号')
    state["group_id"] = int(msg.extract_plain_text().strip())

    if not configer.get_group_status(state["group_id"]):
        await configer_update.finish('群号配置不存在, 已退出更新')

    configer_data = configer.get_config_data(state["group_id"])
    await configer_update.send(f'当前的配置为:\n'
                               f'group_id: {configer_data["group_id"]}\n'
                               f'group_name: {configer_data["group_name"]}\n'
                               f'video_upload_path: {configer_data["video_upload_path"]}\n'
                               f'cover_upload_path: {configer_data["cover_upload_path"]}\n'
                               f'enable_subscribe: {configer_data["enable_subscribe"]}\n'
                               f'subscribe_channel: {configer_data["subscribe_channel"]}')


@configer_update.got("key", prompt="请输入要更新的key")
async def got_update_key(state: T_State, msg: Message = CommandArg()):
    state["key"] = msg.extract_plain_text().strip()

    if not state["key"] in ["group_name", "video_upload_path", "cover_upload_path", "enable_subscribe"]:
        await configer_update.reject('请输入正确的key')


@configer_update.got("value", prompt="请输入新值")
async def got_update_value(state: T_State, msg: Message = CommandArg()):
    state["value"] = msg.extract_plain_text().strip()

    if state["key"] == "enable_subscribe":
        if state["value"] not in ["True", "False"]:
            await configer_update.reject('请输入正确的value, True or False')
        state["value"] = True if state["value"] == "True" else False
    else:
        state["value"] = state["value"]

    await configer.set_config_data(state["group_id"], **{state["key"]: state["value"]})

    await configer_update.finish('更新成功')


@configer_get.handle()
async def handle_configer_get(state: T_State, msg: Message = CommandArg()):
    args = msg.extract_plain_text().strip()  # 首次发送命令时跟随的参数 群号
    if args:
        state["group_id"] = args  # 如果用户发送了参数则直接赋值


@configer_get.got("group_id", prompt="请输入要查询的群号")
async def got_get_group_id(state: T_State, msg: Message = CommandArg()):
    if type(eval(msg.extract_plain_text())) != int:
        await configer_get.reject('请输入正确的群号')
    state["group_id"] = eval(msg.extract_plain_text())

    if not configer.get_group_status(state["group_id"]):
        await configer_get.finish('群号配置不存在, 已退出删除')

    configer_data = configer.get_config_data(state["group_id"])
    await configer_get.finish(f'当前的配置为:\n'
                              f'群号: {configer_data["group_id"]}\n'
                              f'群名: {configer_data["group_name"]}\n'
                              f'视频上传路径: {configer_data["video_upload_path"]}\n'
                              f'封面上传路径: {configer_data["cover_upload_path"]}\n'
                              f'是否开启订阅: {configer_data["enable_subscribe"]}\n'
                              f'订阅列表: {configer_data["subscribe_channel"]}')


@configer_help.handle()
async def handle_configer_help():
    await configer_help.finish('configer 指令\n\n'
                               'list 获取所有配置\n'
                               'get  查询配置\n'
                               'add 添加配置\n'
                               'update 更新配置\n'
                               'delete 删除配置')
