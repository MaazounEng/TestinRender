import asyncio
import os
import sys
import traceback


import aiohttp
from aiohttp import web
import cachetools
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import routing
from gidgethub import sansio
from gidgethub import apps

router = routing.Router()
cache = cachetools.LRUCache(maxsize=500)

routes = web.RouteTableDef()


@routes.get("/", name="home")
async def handle_get(request):
    return web.Response(text="Hello PyLadies Tunis")


@routes.post("/webhook")
async def webhook(request):
    try:
        body = await request.read()
        secret = os.environ.get("GH_SECRET")
        event = sansio.Event.from_http(request.headers, body, secret=secret)
        if event.event == "ping":
            return web.Response(status=200)
        async with aiohttp.ClientSession() as session:
            gh = gh_aiohttp.GitHubAPI(session, "demo", cache=cache)

            await asyncio.sleep(1)
            await router.dispatch(event, gh)
        try:
            print("GH requests remaining:", gh.rate_limit.remaining)
        except AttributeError:
            pass
        print("Webhook received event:", event.event)
        return web.Response(status=200)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        return web.Response(status=500)





if __name__ == "__main__":  # pragma: no cover
    app = web.Application()

    app.router.add_routes(routes)
    port = int(os.environ.get("PORT", 8081))
    if port is not None:
        port = int(port)
    web.run_app(app, port=port)
