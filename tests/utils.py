import logging
import multiprocessing
import socket
import ssl
import time
from contextlib import contextmanager
from typing import NamedTuple, Union, Awaitable, Optional, List, Type

from yarl import URL
import aiohttp
from aiohttp import web

from aiohttp_serve import serve


def is_connectable(url: str):
    url = URL(url)
    if url.scheme == 'unix':  # uds
        family = socket.AF_UNIX
        addr = url.path
    else:  # tcp
        host = url.host
        port = url.port
        if ':' in host:
            family = socket.AF_INET6
        else:
            family = socket.AF_INET
        addr = (host, port)

    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(1)

    try:
        sock.connect(addr)
    except socket.error:
        return False
    else:
        return True
    finally:
        sock.close()


def wait_until_connectable(url: str, timeout=5):
    count = 0
    while not is_connectable(url):
        if count >= timeout:
            raise Exception(f"Couldn't connect to {url} in {timeout} sec.")
        count += 1
        time.sleep(1)
    return True


class Config(NamedTuple):
    app: Union[str, web.Application, Awaitable[web.Application]]
    host: Optional[str] = '127.0.0.1'
    port: Optional[int] = 8080
    bind: Union[str, List[str]] = None
    workers: int = 1
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    log_config: Optional[Union[dict, str]] = None
    access_log_class: Type[web.AbstractAccessLogger] = web.AccessLogger
    access_log_format: str = web.AccessLogger.LOG_FORMAT
    access_log: Optional[logging.Logger] = web.access_logger

    def to_dict(self):
        d = {}
        for key, val in self._asdict().items():
            if val is not None:
                d[key] = val
        return d

    def get_bind_urls(self) -> List[str]:
        if self.bind is not None:
            if isinstance(self.bind, (str, bytes)):
                return [self.bind]
            else:
                return self.bind
        else:
            scheme = 'https' if self.ssl_certfile else 'http'
            return [f'{scheme}://{self.host}:{self.port}']


def run(config: Config):
    serve(**config.to_dict())


@contextmanager
def start_server(config: Config):
    process = multiprocessing.get_context('spawn').Process(target=run, args=(config,))
    process.start()
    for url in config.get_bind_urls():
        wait_until_connectable(url)
    try:
        yield None
    finally:
        process.terminate()
        process.join()


async def fetch(url: str, ssl_context: ssl.SSLContext = None, uds: str = None):
    connector = None
    if uds is not None:
        connector = aiohttp.UnixConnector(path=uds)

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url, ssl=ssl_context) as res:
            return res
