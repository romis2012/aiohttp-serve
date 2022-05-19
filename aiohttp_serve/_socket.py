import os
import socket
import stat
from typing import List

from ._config import Config, BindInfo, BoundSocket
from ._logging import logger


def bind_sockets(config: Config) -> List[BoundSocket]:
    infos = config.get_bind_info()
    sockets = [BoundSocket(socket=bind_socket(i), info=i) for i in infos]
    names = [s.url for s in sockets]
    logger.info(f'Running on {", ".join(names)} (Press CTRL+C to quit)')
    return sockets


def bind_socket(info: BindInfo):
    if info.is_unix_socket:
        path = os.fspath(info.path)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            if stat.S_ISSOCK(os.stat(path).st_mode):
                os.remove(path)
        except FileNotFoundError:
            pass
        except OSError as err:
            # Directory may have permissions only to create socket.
            logger.error('Unable to check or remove stale UNIX socket %r: %r', path, err)
            raise

        try:
            sock.bind(path)
            perms = 0o666
            os.chmod(path, perms)
        except Exception as e:
            sock.close()
            logger.error(e)
            raise
    else:  # http, https
        host = info.host
        port = info.port
        if not host or not port:
            raise ValueError('"host" and "port" should be specified')

        if info.is_ipv6:
            family = socket.AF_INET6
        else:
            family = socket.AF_INET

        sock = socket.socket(family=family)
        # try:
        #     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # except AttributeError:
        #     pass
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except Exception as e:
            sock.close()
            logger.error(e)
            raise

    sock.setblocking(False)
    try:
        sock.set_inheritable(True)
    except AttributeError:
        pass
    return sock


def share_socket(sock: socket.socket) -> socket.socket:
    # Windows requires the socket be explicitly shared across
    # multiple workers (processes).
    from socket import fromshare  # type: ignore

    sock_data = sock.share(os.getpid())  # type: ignore
    return fromshare(sock_data)
