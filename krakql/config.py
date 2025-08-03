from krakql.entities.context import config_ctx
from krakql.entities.interfaces import IConfig


# pylint: disable=too-few-public-methods
class Config(IConfig):
    def __init__(self) -> None:
        super().__init__()
        self._bucket_size: int = 64

        config_ctx.set(self)
