import multiprocessing
import random
import time
from threading import current_thread

import reactivex as rx
from reactivex import operators as op
from reactivex.scheduler import ThreadPoolScheduler


def official_concurrency_example():
    """https://rxpy.readthedocs.io/en/latest/get_started.html#concurrency"""

    def intense_calculation(value):
        # sleep for a random short duration between 0.5 to 2.0 seconds to simulate a long-running calculation
        time.sleep(random.randint(5, 20) * 0.1)
        return value

    # calculate number of CPUs, then create a ThreadPoolScheduler with that number of threads
    optimal_thread_count = multiprocessing.cpu_count()
    pool_scheduler = ThreadPoolScheduler(optimal_thread_count)

    # Create Process 1
    rx.of("Alpha", "Beta", "Gamma", "Delta", "Epsilon").pipe(
        op.map(lambda s: intense_calculation(s)), op.subscribe_on(pool_scheduler)
    ).subscribe(
        on_next=lambda s: print("PROCESS 1: {0} {1}".format(current_thread().name, s)),
        on_error=lambda e: print(e),
        on_completed=lambda: print("PROCESS 1 done!"),
    )

    # Create Process 2
    rx.range(1, 10).pipe(
        op.map(lambda s: intense_calculation(s)), op.subscribe_on(pool_scheduler)
    ).subscribe(
        on_next=lambda i: print("PROCESS 2: {0} {1}".format(current_thread().name, i)),
        on_error=lambda e: print(e),
        on_completed=lambda: print("PROCESS 2 done!"),
    )

    # Create Process 3, which is infinite
    rx.interval(1).pipe(
        op.map(lambda i: i * 100),
        op.observe_on(pool_scheduler),
        op.map(lambda s: intense_calculation(s)),
    ).subscribe(
        on_next=lambda i: print("PROCESS 3: {0} {1}".format(current_thread().name, i)),
        on_error=lambda e: print(e),
    )

    input("Press Enter key to exit\n")


def my_concurrency_test():
    """https://github.com/ReactiveX/RxPY/discussions/659"""
    pool_scheduler = ThreadPoolScheduler(2)

    def num_map(num: int):
        print(f'[num] {current_thread().name} : {num}')
        return num

    num = rx.range(1, 5).pipe(op.map(num_map))

    def name_map(name: str):
        print(f'[name] {current_thread().name} : {name}')
        return name

    name = rx.from_iterable(["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]).pipe(op.map(name_map))

    zipped = rx.zip(num, name)
    merged = rx.merge(num, name)

    merged.pipe(op.subscribe_on(pool_scheduler)).subscribe(
        on_next=lambda i: print("consumer: {0} {1}".format(current_thread().name, i))
    )

    input("Press Enter key to exit\n")
