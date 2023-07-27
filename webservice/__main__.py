import os
import asyncio
import aiohttp
from aiohttp import web
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import routing
from gidgethub import apps

router = routing.Router()

routes = web.RouteTableDef()

async def handle_pull_request_event(payload):
    # Add your pull request event handling logic here
    # For example, you can post a comment on the pull request
    pass

@routes.post("/webhook")
async def webhook(request):
    try:
        body = await request.read()
        secret = os.environ.get("GH_SECRET")
        event = sansio.Event.from_http(request.headers, body, secret=secret)
        if event.event == "ping":
            return web.Response(status=200)
        
        async with aiohttp.ClientSession() as session:
            gh = gh_aiohttp.GitHubAPI(
                session,
                "MaazounEng",  # Your GitHub App's name
                oauth_token=await apps.get_installation_access_token(
                    gh, 
                    app_id=os.environ.get("GH_APP_ID"), 
                    private_key=os.environ.get("GH_PRIVATE_KEY")
                )
            )

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

app = web.Application()
app.router.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
