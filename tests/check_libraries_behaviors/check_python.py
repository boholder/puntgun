import functools


def is_cached_value_remain_same_pointer():
    @functools.lru_cache(maxsize=1)
    def get():
        return [1, 2, 3]

    # yes
    first = get()
    print(first)
    second = get()
    print(second)
    assert id(first) == id(second)
