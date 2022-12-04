import asyncio
import functools
import os
from typing import Any

import aiohttp
import tweepy.asynchronous.client as tweepy_async_client_module
from tweepy.asynchronous import AsyncClient as TweepyAsyncClient

from client import USER_API_PARAMS, response_to_users
from puntgun.conf import encrypto, secret
from puntgun.rules.data import User


class AsyncClient:
    def __init__(self, tweepy_client: TweepyAsyncClient):
        self.clt = tweepy_client
        self.me = User()
        self.id = 0
        self.name = ""

    async def _get_my_info(self) -> None:
        resp = await self.clt.get_me()
        self.me = User.from_response(resp.data)
        self.id = self.me.id
        self.name = self.me.name

    @staticmethod
    @functools.lru_cache(maxsize=1)
    async def singleton() -> "AsyncClient":
        secrets = secret.load_or_request_all_secrets(encrypto.load_or_generate_private_key())
        client = AsyncClient(
            TweepyAsyncClient(
                consumer_key=secrets["ak"],
                consumer_secret=secrets["aks"],
                access_token=secrets["at"],
                access_token_secret=secrets["ats"],
                wait_on_rate_limit=True,
            )
        )
        await client._get_my_info()
        return client

    async def get_users_by_usernames(self, names: list[str]) -> list[User]:
        """
        Query users information.
        **Rate limit: 900 / 15 min**
        https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
        """
        if len(names) > 100:
            raise ValueError("at most 100 usernames per request")

        return response_to_users(await self.clt.get_users(usernames=names, **USER_API_PARAMS))


# def call_the_users_lookup_client_api(param: list, client_func: Callable[[list], list[User]]) -> rx.Observable[User]:
#     return rx.from_iterable(param).pipe(
#         # Some Twitter APIs limit the number of query targets in a single request.
#         # For now, we only use the users lookup API which set its limit on one hundred, so we'll hard-code it.
#         op.buffer_with_count(100),
#         # log for debug
#         op.do(rx.Observer(on_next=lambda users: logger.debug("Batch of targets to client: {}", users))),
#         op.map(client_func),
#         op.flat_map(lambda x: x),
#         op.do(rx.Observer(on_next=lambda u: logger.debug("Users from client: {}", u))),
#     )


def let_aiohttp_client_session_uses_system_proxy_if_proxy_is_set() -> None:
    """
    aiohttp won't use the system proxy by default,
    and it seems that the only way to make it to use the proxy is
    passing the "trust_env=True" parameter while creating aiohttp.ClientSession objects.

    tweepy.asynchronous.AsyncClient isn't pass the "trust_env" parameter,
    so we'll risk ourselves to fix it manually,
    thx to Python's dynamic character, we can make it happen.
    """

    http_proxy_is_set = os.environ["HTTP_PROXY"]
    if http_proxy_is_set:
        class ProxyClientSession(aiohttp.ClientSession):
            def __init__(self, *args: Any, **kwargs: Any):
                super().__init__(*args, **kwargs, trust_env=True)

        aiohttp.ClientSession = ProxyClientSession
        tweepy_async_client_module.aio_http = aiohttp


let_aiohttp_client_session_uses_system_proxy_if_proxy_is_set()


# --------------


async def main() -> None:
    client = await AsyncClient.singleton()
    print(await client.get_users_by_usernames(["TwitterDev"]))


asyncio.run(main())
