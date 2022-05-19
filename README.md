## aiohttp-serve

`aiohttp-serve` package allows you to run `aiohttp.web.Application` on multiple workers/processes 
(if for some reason you don't want to use external servers such as gunicorn etc.)

## Requirements
- Python >= 3.7
- aiohttp >= 3.7.4
- PyYAML>=5.4.1 (optional)

## Installation
```
pip install aiohttp-serve
```

## Usage

<h5><code>web.py</code></h5>

```python
from aiohttp import web


async def index(request):
    return web.Response(body='Hello world')


app = web.Application()
app.router.add_get('/', index)
```

#### simple usage:

```python
from aiohttp_serve import serve

if __name__ == '__main__':
    serve(
        'web:app',
        host='127.0.0.1',
        port=8080,
        workers=4,
    )
```

#### bind to multiple host/port/path:

```python
from aiohttp_serve import serve

if __name__ == '__main__':
    serve(
        'web:app',
        bind=[
            'http://127.0.0.1:80',
            'https://127.0.0.1:443',
            'unix:/path/to/unix/socket.sock',
        ],
        workers=4,
        ssl_certfile='/path/to/cert.crt',
        ssl_keyfile='/path/to/key.key',
    )
```

#### logging:

Just configure logging at module level

```python
import yaml
import logging.config

from aiohttp_serve import serve

with open('./examples/logging.yaml', mode='r') as f:
    logging.config.dictConfig(yaml.safe_load(f))

if __name__ == '__main__':
    serve(
        'web:app',
        host='127.0.0.1',
        port=8080,
        workers=4,
    )
```

of use `log_config` arg (dict, .json or .yaml or .conf file)

```python
from aiohttp_serve import serve

if __name__ == '__main__':
    serve(
        'web:app',
        host='127.0.0.1',
        port=8080,
        workers=4,
        log_config='./examples/logging.yaml',
    )
```