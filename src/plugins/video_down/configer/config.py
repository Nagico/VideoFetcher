from pydantic import BaseSettings


class Config(BaseSettings):
    # 配置文件
    video_config_file: str = ""  # 下载配置文件

    class Config:
        extra = "ignore"
