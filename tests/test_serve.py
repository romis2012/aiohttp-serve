import pytest
from yarl import URL

from tests.utils import Config, start_server, fetch

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8080
DEFAULT_HTTP_URL = f'http://{DEFAULT_HOST}:{DEFAULT_PORT}/'
DEFAULT_HTTPS_URL = f'https://{DEFAULT_HOST}:{DEFAULT_PORT}/'

DEFAULT_APP = 'tests.app:app'


@pytest.mark.asyncio
async def test_simple_multiple_workers():
    config = Config(
        DEFAULT_APP,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        workers=2,
    )
    with start_server(config):
        res = await fetch(url=DEFAULT_HTTP_URL)
        assert res.status == 200


@pytest.mark.asyncio
async def test_app_factory():
    config = Config(
        'tests.app:app_factory()',
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        workers=2,
    )
    with start_server(config):
        res = await fetch(url=DEFAULT_HTTP_URL)
        assert res.status == 200


@pytest.mark.asyncio
async def test_async_app_factory():
    config = Config(
        'tests.app:async_app_factory()',
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        workers=2,
    )
    with start_server(config):
        res = await fetch(url=DEFAULT_HTTP_URL)
        assert res.status == 200


@pytest.mark.asyncio
async def test_ssl_cert_and_key(ssl_certfile, ssl_keyfile, client_ssl_context):
    config = Config(
        DEFAULT_APP,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )
    with start_server(config):
        res = await fetch(url=DEFAULT_HTTPS_URL, ssl_context=client_ssl_context)
        assert res.status == 200


@pytest.mark.asyncio
async def test_ssl_cert_chain(ssl_key_and_cert_chain, client_ssl_context):
    config = Config(
        DEFAULT_APP,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        ssl_certfile=ssl_key_and_cert_chain,
    )
    with start_server(config):
        res = await fetch(url=DEFAULT_HTTPS_URL, ssl_context=client_ssl_context)
        assert res.status == 200


@pytest.mark.asyncio
async def test_ssl_ca_certs(ssl_key_and_cert_chain, ssl_ca_cert, client_ssl_context):
    config = Config(
        DEFAULT_APP,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        ssl_certfile=ssl_key_and_cert_chain,
        ssl_ca_certs=ssl_ca_cert,
    )
    with start_server(config):
        res = await fetch(url=DEFAULT_HTTPS_URL, ssl_context=client_ssl_context)
        assert res.status == 200


@pytest.mark.asyncio
async def test_bind_single_host(ssl_certfile, ssl_keyfile, client_ssl_context):
    bind_url = f'https://{DEFAULT_HOST}:{DEFAULT_PORT}'
    config = Config(
        'tests.app:app',
        bind=bind_url,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )
    with start_server(config):
        res = await fetch(url=bind_url, ssl_context=client_ssl_context)
        assert res.status == 200


@pytest.mark.asyncio
async def test_bind_multiple_hosts(ssl_certfile, ssl_keyfile, client_ssl_context):
    bind = [
        'http://127.0.0.1:8080',
        'https://127.0.0.1:8081',
        'http://[::1]:9090',
        'https://[::1]:9091',
        'unix:/tmp/sock.sock',
    ]
    config = Config(
        'tests.app:app',
        bind=bind,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )
    with start_server(config):
        for b in bind:
            uds = None
            ssl_context = None
            parsed_url = URL(b)
            if parsed_url.scheme == 'unix':
                url = 'http://*/'
                uds = parsed_url.path
            else:
                url = str(parsed_url)
                if parsed_url.scheme == 'https':
                    ssl_context = client_ssl_context

            res = await fetch(url=url, ssl_context=ssl_context, uds=uds)
            assert res.status == 200
