import logging
import os
import socket
import ssl

from aiohttp import web
from yarl import URL
from typing import Optional, NamedTuple, Union, List, Type


class BindInfo:
    def __init__(self, url: str):
        self.url = URL(url)

    @property
    def scheme(self) -> str:
        return self.url.scheme

    @property
    def host(self) -> str:
        return self.url.host

    @property
    def port(self) -> int:
        return self.url.port

    @property
    def path(self) -> str:
        return self.url.path

    @property
    def is_ssl(self) -> bool:
        return self.scheme.startswith('https')

    @property
    def is_unix_socket(self):
        return self.scheme == 'unix'

    @property
    def is_ipv6(self):
        return self.host and ':' in self.host


class BoundSocket(NamedTuple):
    socket: socket.socket
    info: BindInfo

    @property
    def url(self):
        return str(self.info.url)

    def close(self):
        self.socket.close()
        if self.info.is_unix_socket:
            try:
                os.remove(self.info.path)
            except FileNotFoundError:
                pass


class Config:
    def __init__(
        self,
        host: Optional[str] = '127.0.0.1',
        port: Optional[int] = 8080,
        bind: Union[str, List[str]] = None,
        workers: int = 1,
        use_uvloop: bool = True,
        ssl_certfile: Optional[str] = None,
        ssl_keyfile: Optional[str] = None,
        ssl_keyfile_password: Optional[str] = None,
        ssl_version: int = ssl.PROTOCOL_TLS_SERVER,
        ssl_verify_mode: int = ssl.CERT_NONE,
        ssl_ca_certs: Optional[str] = None,
        ssl_ciphers: str = 'TLSv1',
        shutdown_timeout: float = 60.0,
        keepalive_timeout: float = 75.0,
        backlog: int = 128,
        log_config: Optional[Union[dict, str]] = None,
        access_log_class: Type[web.AbstractAccessLogger] = web.AccessLogger,
        access_log_format: str = web.AccessLogger.LOG_FORMAT,
        access_log: Optional[logging.Logger] = web.access_logger,
        handle_signals: bool = True,
    ):
        self.host = host
        self.port = port
        self.bind = bind

        self.workers = workers
        self.use_uvloop = use_uvloop
        self.ssl_certfile = ssl_certfile
        self.ssl_keyfile = ssl_keyfile
        self.ssl_keyfile_password = ssl_keyfile_password
        self.ssl_version = ssl_version
        self.ssl_verify_mode = ssl_verify_mode
        self.ssl_ca_certs = ssl_ca_certs
        self.ssl_ciphers = ssl_ciphers

        self.shutdown_timeout = shutdown_timeout
        self.keepalive_timeout = keepalive_timeout
        self.backlog = backlog

        self.log_config = log_config
        self.access_log_class = access_log_class
        self.access_log_format = access_log_format
        self.access_log = access_log

        self.handle_signals = handle_signals

    @property
    def is_ssl(self) -> bool:
        return bool(self.ssl_certfile and self.ssl_keyfile)

    def create_ssl_context(self) -> Optional[ssl.SSLContext]:
        if self.is_ssl:
            ctx = ssl.SSLContext(self.ssl_version)
            get_password = (
                (lambda: self.ssl_keyfile_password) if self.ssl_keyfile_password else None
            )
            ctx.load_cert_chain(self.ssl_certfile, self.ssl_keyfile, get_password)
            ctx.verify_mode = self.ssl_verify_mode
            if self.ssl_ca_certs:
                ctx.load_verify_locations(self.ssl_ca_certs)
            if self.ssl_ciphers:
                ctx.set_ciphers(self.ssl_ciphers)
            return ctx
        else:
            return None

    def get_bind_info(self) -> List[BindInfo]:
        if self.bind is not None:
            if isinstance(self.bind, (str, bytes)):
                return [BindInfo(self.bind)]
            else:
                return [BindInfo(url) for url in self.bind]
        else:
            scheme = 'https' if self.is_ssl else 'http'
            return [BindInfo(f'{scheme}://{self.host}:{self.port}')]
