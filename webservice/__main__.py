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



@routes.post("/webhook")
async def webhook(request):
    try:
        body = await request.read()
        secret = os.environ.get("GH_SECRET")
        event = sansio.Event.from_http(request.headers, body, secret=secret)
        if event.event == "ping":
            return web.Response(status=200)
        async with aiohttp.ClientSession() as session:
            gh = gh_aiohttp.GitHubAPI(session, "MaazounEng", cache=cache)

            await asyncio.sleep(1)
            await router.dispatch(event, gh)
        try:
            print("GH requests remaining:", gh.rate_limit.remaining)
        except AttributeError:
            pass
        return web.Response(status=200)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        return web.Response(status=500)



@router.register("pull_request", action="opened")
async def pr_opened(event, gh, *args, **kwargs):
    issue_url = event.data["pull_request"]["issue_url"]
    username = event.data["sender"]["login"]
    installation_id = event.data["installation"]["id"]

    installation_access_token = await apps.get_installation_access_token(
        gh,
        installation_id=installation_id,
        app_id=os.environ.get("GH_APP_ID"),
        private_key=os.environ.get("GH_PRIVATE_KEY"),
    )
    author_association = event.data["pull_request"]["author_association"]
    if author_association == "NONE":
        # first time contributor
        msg = f"Thanks for your first contribution @{username}"
    else:
        # seasoned contributor
        msg = f"Welcome back, @{username}. You are a {author_association}."
    response = await gh.post(
        f"{issue_url}/comments",
        data={"body": msg},
        oauth_token=installation_access_token["token"],
    )


if __name__ == "__main__":  # pragma: no cover
    app = web.Application()

    app.router.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)
    web.run_app(app, port=port)
