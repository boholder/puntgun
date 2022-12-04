import asyncio
import time
from collections import namedtuple

import reactivex as rx
from reactivex import operators as op
from reactivex.disposable import Disposable
from reactivex.scheduler.eventloop import AsyncIOScheduler
from reactivex.subject import Subject

start = time.time()


def ts():
    return f"{time.time() - start:.3f}"


ACTION_DURATION = 1.0

first_subject = Subject()
first_async_action = Subject()
second_subject = Subject()

Data = namedtuple("Data", ["api", "param", "future"])


async def async_calling_api(data: Data):
    """Some async processing, like sending/writing data."""
    print(f"{ts()} [A]sync action started  api:{data.api} param:{data.param}")
    # process the data with async function
    await asyncio.sleep(ACTION_DURATION)
    print(f"{ts()} [A]sync action finished api:{data.api} param:{data.param}")
    # process finished, return the response
    return f"[{data.param}]"


def serialize_map_async(mapper):
    def _serialize_map_async(source):
        def on_subscribe(observer, scheduler):
            # separate different api callings into different task queues
            queues = {k: asyncio.Queue() for k in range(0, 3)}

            async def infinite_loop(q: asyncio.Queue[Data]):
                try:
                    while True:
                        data = await q.get()
                        resp = await mapper(data)
                        observer.on_next(resp)
                        data.future.set_result(resp)
                except Exception as e:
                    observer.on_error(e)

            def on_next(data: Data):
                # take data from upstream ( calls on subject.on_next() trigger it )
                # synchronous -> asynchronous by putting elements into queue
                try:
                    queues[data.api].put_nowait(data)
                except Exception as e:
                    observer.on_error(e)

            tasks = [asyncio.create_task(infinite_loop(q)) for q in queues.values()]

            d = source.subscribe(
                on_next=on_next,
                on_error=observer.on_error,
                on_completed=observer.on_completed,
            )

            def dispose():
                d.dispose()
                [task.cancel() for task in tasks]

            return Disposable(dispose)

        return rx.create(on_subscribe)

    return _serialize_map_async


async def setup():
    """Setting up the Rx subject to make sure all work is done
    in sequence without overlaps.
    """

    loop = asyncio.get_event_loop()
    first_subject.pipe(
        serialize_map_async(async_calling_api),
        # The futures created here was not waited for, so it was not added to asyncio's chain,
        # resulting in the following gather only guaranteeing all the tasks of the first level,
        # and some second level task was canceled before it was executed.
        op.do_action(lambda x: second_subject.on_next(Data(2, x, asyncio.Future()))),
    ).subscribe(
        on_next=lambda param: print(f"{ts()} [O]bserver [1] received: {param}"),
        scheduler=AsyncIOScheduler(loop)
    )

    second_subject.pipe(serialize_map_async(async_calling_api), ).subscribe(
        on_next=lambda param: print(f"{ts()} [O]bserver [2] received: {param}"),
        scheduler=AsyncIOScheduler(loop)
    )


async def add(api: int, param: str):
    future = asyncio.Future()
    first_subject.on_next(Data(api, param, future))
    return await future


async def main():
    await setup()
    # I wonder if there is a way to write "await rx.from..."
    #
    # rx.from_iterable("a", "b").pipe(
    #  op.do(await ...)
    # )

    a = await asyncio.gather(add(0, "0a"), add(0, "0b"), add(1, "1a"), add(1, "1b"), )
    print(f"---> {a}")


asyncio.run(main())
