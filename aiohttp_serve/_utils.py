import sys
from importlib import import_module
from pathlib import Path
from typing import Union, Awaitable

from aiohttp import web


class NoAppError(Exception):
    pass


def load_application(
    path: Union[str, web.Application, Awaitable[web.Application]]
) -> Union[web.Application, Awaitable[web.Application]]:
    """
    Taken from hypercorn.utils.load_application
    """
    if not isinstance(path, str):
        return path

    try:
        module_name, app_name = path.split(":", 1)
    except ValueError:
        module_name, app_name = path, "app"
    except AttributeError:
        raise NoAppError()

    module_path = Path(module_name).resolve()
    sys.path.insert(0, str(module_path.parent))
    if module_path.is_file():
        import_name = module_path.with_suffix("").name
    else:
        import_name = module_path.name
    try:
        module = import_module(import_name)
    except ModuleNotFoundError as error:
        if error.name == import_name:
            raise NoAppError()
        else:
            raise

    try:
        return eval(app_name, vars(module))
    except NameError:
        raise NoAppError()
