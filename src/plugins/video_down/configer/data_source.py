import os
import json
import aiofiles
from nonebot.log import logger

from ..exception import ConfigSaveError


class Configer:
    """
    配置文件处理类

    Attributes:
        config_path: 配置文件路径
        config_data: 配置文件内容

    Config Data:
        :key: 群号
        :value: {
            video_upload_path:str 视频上传路径
            cover_upload_path:str 封面上传路径
            enable_subscribe:bool 是否开启订阅
            subscribe_channel:list 订阅的频道
        }

    """

    INIT_CONFIG = {
        "group_id": 0,
        "group_name": "",
        "video_upload_path": "",
        "cover_upload_path": "",
        "enable_subscribe": False,
        "subscribe_channel": []
    }

    def __init__(self, config_path):
        self.config_path = config_path
        self.config_data = None
        self.read_config_file()

    def read_config_file(self):
        """
        读取配置文件
        """
        # 已加载过配置文件
        if self.config_data is not None:
            return

        # 如果配置文件不存在
        if not os.path.exists(self.config_path):
            logger.warning(f'配置文件不存在，创建默认配置文件：{self.config_path}')
            try:
                if not os.path.exists(os.path.dirname(os.path.abspath(self.config_path))):  # 文件夹不存在
                    os.makedirs(os.path.dirname(self.config_path))  # 创建文件夹

                with open(self.config_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps({}, ensure_ascii=False, indent=4))  # 创建空配置文件

            except Exception as e:  # 创建失败
                logger.error(f'创建配置文件{self.config_path}失败：{e}')
                logger.warning('使用默认配置文件 {}')
                self.config_data = {}
                return

        # 读取文件
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.loads(f.read())  # 读取配置文件
                logger.debug(f'读取配置文件：{self.config_path}')

        except Exception as e:  # 读取失败
            logger.error(f'读取配置文件{self.config_path}失败：{e}')
            logger.warning('使用默认配置文件 {}')
            self.config_data = {}
            return

    async def save_config_file(self):
        """
        保存配置文件

        :exception ConfigSaveError: 保存配置文件失败
        """
        try:
            async with aiofiles.open(self.config_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self.config_data, ensure_ascii=False, indent=4))
                logger.debug(f'保存配置文件：{self.config_path}\n内容：{self.config_data}')
        except Exception as e:  # 保存失败
            logger.error(f'保存配置文件{self.config_path}失败：{e}')
            logger.warning(f'当前配置文件内容：{self.config_data}')
            raise ConfigSaveError(f'保存配置文件{self.config_path}失败：{e}', self.config_data)

    def get_group_status(self, group_id: int) -> bool:
        """
        获取qq群是否在配置文件中

        :param group_id: 群号

        :return: 是否存在
        """
        return group_id in self.config_data

    def get_config_data(self, group_id=None) -> dict:
        """
        获取配置文件内容

        :param group_id: 群号

        :return: 配置文件内容
        """
        if group_id is None:  # 获取全部配置
            return self.config_data
        if type(group_id) == int:  # 字符串化
            group_id = str(group_id)
        if group_id in self.config_data:  # 获取指定配置
            return self.config_data[group_id]
        return {}  # 没有配置

    async def set_config_data(self, group_id, group_name: str = None, video_upload_path: str = None,
                              cover_upload_path: str = None, enable_subscribe: bool = None) -> None:
        """
        设置配置信息

        :param group_id: 群号

        :param group_name: 群名

        :param video_upload_path: 视频上传路径

        :param cover_upload_path: 封面上传路径

        :param enable_subscribe: 是否开启订阅
        """
        if type(group_id) == int:  # 字符串化
            group_id = str(group_id)

        if group_id not in self.config_data:  # 不存在该群配置
            self.config_data[group_id] = Configer.INIT_CONFIG
            self.config_data[group_id]['group_id'] = group_id

        # 更新配置
        if group_name:
            self.config_data[group_id]['group_name'] = group_name
        if video_upload_path:
            self.config_data[group_id]['video_upload_path'] = video_upload_path
        if cover_upload_path:
            self.config_data[group_id]['cover_upload_path'] = cover_upload_path
        if enable_subscribe:
            self.config_data[group_id]['enable_subscribe'] = enable_subscribe

        await self.save_config_file()

    def delete_config_data(self, group_id):
        """
        删除配置

        :param group_id: 群号
        """
        if type(group_id) == int:  # 字符串化
            group_id = str(group_id)

        if group_id in self.config_data:
            self.config_data.pop(group_id)
            self.save_config_file()

    def get_subscribe_channel(self, group_id):
        """
        获取订阅列表

        :param group_id: 群号

        :return: 列表引用
        """
        if type(group_id) == int:  # 字符串化
            group_id = str(group_id)

        if group_id in self.config_data:  # 获取指定配置
            return self.config_data[group_id]['subscribe_channel']  # 返回引用
        return None
