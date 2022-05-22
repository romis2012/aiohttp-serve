import asyncio

from aiohttp import web


async def index(request):
    return web.Response(body='Index')


app = web.Application()
app.router.add_get('/', index)


def app_factory():
    result = web.Application()
    result.router.add_get('/', index)
    return result


async def async_app_factory():
    await asyncio.sleep(0.1)
    result = web.Application()
    result.router.add_get('/', index)
    return result
