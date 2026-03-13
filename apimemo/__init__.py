from importlib.metadata import version

from apimemo.config import ApiMemoConfig, configure, get_config

__version__ = version("apimemo")

__all__ = [
    "__version__",
    "ApiMemoConfig",
    "configure",
    "get_config",
]
