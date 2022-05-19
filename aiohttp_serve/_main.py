from typing import Optional, Union, List, Awaitable

from aiohttp import web

from ._config import Config
from ._logging import configure_logging
from ._socket import bind_sockets
from ._supervisor import Supervisor
from ._worker import Worker


def serve(
    app: Union[str, web.Application, Awaitable[web.Application]],
    *,
    host: Optional[str] = '127.0.0.1',
    port: Optional[int] = 8080,
    bind: Union[str, List[str]] = None,
    workers: int = 1,
    **kwargs,
):
    config = Config(host=host, port=port, bind=bind, workers=workers, **kwargs)
    configure_logging(config.log_config)

    sockets = bind_sockets(config)
    if config.workers > 1:
        Supervisor(app, sockets=sockets, config=config).run()
    else:
        Worker(app, sockets=sockets, config=config).run()

    for s in sockets:
        s.close()
