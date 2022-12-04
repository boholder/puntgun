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
Data = namedtuple("Data", ["id", "future"])
subject = Subject()
subject2 = Subject()

APICalling = namedtuple("APICalling", ["api", "future"])


async def async_action(id: int = 0):
    """Some async processing, like sending/writing data."""
    print(f"{ts()} Async action  started {id}")
    await asyncio.sleep(ACTION_DURATION)
    print(f"{ts()} Async action finished {id}")
    return id


def serialize_map_async(mapper):
    def _serialize_map_async(source):
        def on_subscribe(observer, scheduler):
            q = asyncio.Queue()

            async def map_async(q):
                try:
                    while True:
                        i = await q.get()
                        ii = await mapper(i.id)
                        observer.on_next(ii)
                        i.future.set_result(ii)
                except Exception as e:
                    observer.on_error(e)

            def on_next(i):
                try:
                    q.put_nowait(i)
                except Exception as e:
                    observer.on_error(e)

            task = asyncio.create_task(map_async(q))
            d = source.subscribe(
                on_next=on_next,
                on_error=observer.on_error,
                on_completed=observer.on_completed,
            )

            def dispose():
                d.dispose()
                task.cancel()

            return Disposable(dispose)

        return rx.create(on_subscribe)

    return _serialize_map_async


async def setup():
    """Setting up the Rx subject to make sure all work is done
    in sequence without overlaps.
    """

    subject.pipe(
        serialize_map_async(async_action),
        op.map(lambda x: f"{x} <-"),
        op.do_action(lambda x: subject2.on_next(Data(f"-> {x}", asyncio.Future()))),
    ).subscribe(
        on_next=lambda item: print("observer [1] received:", item), scheduler=AsyncIOScheduler(asyncio.get_event_loop())
    )

    subject2.pipe(serialize_map_async(async_action), ).subscribe(
        on_next=lambda item: print("observer [2] received:", item), scheduler=AsyncIOScheduler(asyncio.get_event_loop())
    )


async def add(id: int):
    """Add "some work" and await until it is done."""
    future = asyncio.Future()
    subject.on_next(Data(id, future))
    return await future


async def main():
    await setup()

    # add work in any fashion (code I cannot influence)
    print(f"{ts()} before 1")
    await add(1)
    print(f"{ts()} after  1")

    await asyncio.sleep(0.1)

    print(f"{ts()} before 2")
    await add(2)
    print(f"{ts()} after  2")

    print(f"{ts()} before 4, 5, 6")
    await asyncio.gather(add(4), add(5), add(6))
    print(f"{ts()} after  4, 5, 6")


asyncio.run(main())
