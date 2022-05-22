import multiprocessing
import os
import platform
import random
import time
from typing import List
import signal

from aiohttp.web_runner import GracefulExit

from ._config import Config, BoundSocket
from ._logging import logger, configure_logging
from ._worker import Worker

multiprocessing.allow_connection_pickling()


def shutdown(sig, frame):  # noqa
    raise GracefulExit()


def run_worker(
    app: str,
    *,
    sockets: List[BoundSocket],
    config: Config,
):
    configure_logging(config.log_config)
    Worker(app, sockets=sockets, config=config).run()


class Supervisor:
    def __init__(
        self,
        app: str,
        *,
        sockets: List[BoundSocket],
        config: Config,
        start_method='spawn',
    ):
        self.app = app
        self.sockets = sockets
        self.config = config

        self.context = multiprocessing.get_context(start_method)

    def run(self):
        signal.signal(signal.SIGTERM, shutdown)

        logger.info(f'Starting master process [{os.getpid()}]')
        processes = []
        for i in range(self.config.workers):
            process = self.context.Process(
                target=run_worker,
                kwargs=dict(app=self.app, sockets=self.sockets, config=self.config),
            )
            process.daemon = True
            process.start()
            processes.append(process)

            if platform.system() == 'Windows':  # pragma: no cover
                time.sleep(0.1 * random.random())

        try:
            for process in processes:
                process.join()
        except (SystemExit, KeyboardInterrupt):
            logger.info(f'Stopping master process [{os.getpid()}]')
            pass
        finally:
            for process in processes:
                process.terminate()
                logger.info(f'Finished worker process [{process.pid}]')

        logger.info(f'Finished master process [{os.getpid()}]')
