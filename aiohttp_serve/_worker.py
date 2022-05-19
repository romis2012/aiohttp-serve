import asyncio
import os
import platform
import sys
from typing import Union, Awaitable, List

from aiohttp import web

from ._config import Config, BoundSocket
from ._logging import logger
from ._utils import load_application
from ._socket import share_socket


class Worker:
    def __init__(
        self,
        app: Union[str, web.Application, Awaitable[web.Application]],
        *,
        sockets: List[BoundSocket],
        config: Config,
    ):
        self.app = load_application(app)
        self.sockets = sockets
        self.config = config
        self.loop: asyncio.AbstractEventLoop = None  # type: ignore

    def run(self):
        logger.info(f'Starting worker process [{os.getpid()}]')

        self.loop = self._setup_loop()

        main_task = self.loop.create_task(self._run_app())
        try:
            self.loop.run_until_complete(main_task)
        except (SystemExit, KeyboardInterrupt):
            logger.info(f'Stopping worker process [{os.getpid()}]')
            pass
        finally:
            self._shutdown()

    async def _run_app(self):
        app = self.app
        config = self.config
        sockets = self.sockets

        if asyncio.iscoroutine(app):
            app = await app  # type: ignore[misc]

        runner = web.AppRunner(
            app,
            handle_signals=config.handle_signals,
            access_log_class=config.access_log_class,
            access_log_format=config.access_log_format,
            access_log=config.access_log,
            keepalive_timeout=config.keepalive_timeout,
        )

        await runner.setup()

        ssl_context = config.create_ssl_context()

        sites: List[web.BaseSite] = []
        try:
            for s in sockets:
                is_ssl = s.info.is_ssl

                if is_ssl and ssl_context is None:
                    raise ValueError(
                        f'ssl_context should be specified for https site: {s.info.url}'
                    )

                sock = s.socket
                if config.workers > 1 and platform.system() == 'Windows':
                    sock = share_socket(s.socket)

                sites.append(
                    web.SockSite(
                        runner,
                        sock,
                        shutdown_timeout=config.shutdown_timeout,
                        ssl_context=ssl_context if is_ssl else None,
                        backlog=config.backlog,
                    )
                )

            for site in sites:
                await site.start()

            # sleep forever by 1 hour intervals,
            # on Windows before Python 3.8 wake up every 1 second to handle
            # Ctrl+C smoothly
            if platform.system() == 'Windows' and sys.version_info < (3, 8):
                delay = 1
            else:
                delay = 3600

            while True:
                await asyncio.sleep(delay)
        finally:
            await runner.cleanup()

    def _setup_loop(self) -> asyncio.AbstractEventLoop:
        config = self.config

        if config.use_uvloop:
            try:
                import uvloop  # noqa

                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            except ImportError:
                pass

        if config.workers > 1 and platform.system() == 'Windows':
            warn_msg = (
                'Using workers > 1 on Windows will force the use '
                'of SelectorEventLoop due to some issues '
                'with "shared" sockets in ProactorEventLoop'
            )
            # warnings.warn(warn_msg, RuntimeWarning, stacklevel=2)
            logger.warning(warn_msg)
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type: ignore

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        return loop

    def _shutdown(self):
        loop = self.loop
        self._cancel_all_tasks()
        loop.run_until_complete(loop.shutdown_asyncgens())
        try:
            loop.run_until_complete(loop.shutdown_default_executor())
        except AttributeError:
            pass  # shutdown_default_executor is new to Python 3.9
        loop.close()

    def _cancel_all_tasks(self):
        loop = self.loop

        tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
        if not tasks:
            return

        for task in tasks:
            task.cancel()

        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

        for task in tasks:
            if task.cancelled():
                continue
            if task.exception() is not None:
                loop.call_exception_handler(
                    {
                        "message": "unhandled exception during asyncio.run() shutdown",
                        "exception": task.exception(),
                        "task": task,
                    }
                )
