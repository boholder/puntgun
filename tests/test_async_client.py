import asyncio

from puntgun.async_client import AsyncClient


async def main() -> None:
    client = await AsyncClient.singleton()
    print(client.me)


asyncio.run(main())
