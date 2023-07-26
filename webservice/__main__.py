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

async def close_issue(gh, "MaazounEng","A_test", 1):
    """
    Closes an open issue on GitHub.

    Args:
        gh: A `gh_aiohttp.GitHubAPI` object.
        repo_owner: The owner of the repository.
        repo_name: The name of the repository.
        issue_number: The number of the issue to close.
    """
    await gh.patch(f"/repos/{repo_owner}/{repo_name}/issues/{issue_number}",
                   data={"state": "closed"})


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

            if event.event == "issues":
                action = event.data["action"]
                if action == "closed":
                    return web.Response(status=200)
                elif action == "opened":
                    repo_owner = event.data["repository"]["owner"]["login"]
                    repo_name = event.data["repository"]["name"]
                    issue_number = event.data["issue"]["number"]
                    await close_issue(gh, repo_owner, repo_name, issue_number)
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
