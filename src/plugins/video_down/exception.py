# 自定义异常

class VideoDownException(Exception):
    """
    异常基类
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class ConfigSaveError(VideoDownException):
    """
    配置文件保存异常
    """
    def __init__(self, msg, data=None):
        self.message = msg
        self.data = data  # 当前配置信息


class DownloadException(VideoDownException):
    """
    下载异常
    """
    pass


class UploadException(VideoDownException):
    """
    上传异常
    """
    pass


class InfoException(VideoDownException):
    """
    信息获取异常
    """
    pass
