"""Deterministic synthetic inputs for search tests and benchmarks."""

from __future__ import annotations

from random import Random


GENERATOR_VERSION = 3
DUPLICATE_POLICY = "sample_with_replacement_from_signed_even_pool_max_1_n_div_3"
MISS_POLICY = "seeded_mix_below_internal_gap_and_above_observed_ids"


def generate_search_case(
    array_size: int,
    query_count: int,
    *,
    seed: int,
    hit_rate: float = 0.5,
) -> tuple[list[int], list[int]]:
    """Return an unsorted ID list and ordered queries of requested sizes.

    The generator intentionally draws IDs from a smaller value pool so that
    larger inputs contain duplicates. The requested hit count is rounded to the
    nearest representable integer, with halves rounded up. A local
    random-number generator prevents changes to global random state.
    """

    if array_size < 0:
        raise ValueError("array_size must be non-negative")
    if query_count < 0:
        raise ValueError("query_count must be non-negative")
    if not 0.0 <= hit_rate <= 1.0:
        raise ValueError("hit_rate must be between 0 and 1")

    random = Random(seed)
    value_pool_size = max(1, array_size // 3)
    value_pool = [
        2 * (index - value_pool_size // 2)
        for index in range(value_pool_size)
    ]
    ids = [random.choice(value_pool) for _ in range(array_size)]

    # A one-query 50% scenario cannot literally be mixed. Rounding half up
    # selects one hit; the benchmark records both requested and realized rates.
    hit_count = int(query_count * hit_rate + 0.5) if ids else 0
    hits = [random.choice(ids) for _ in range(hit_count)]

    miss_count = query_count - hit_count
    misses: list[int] = []
    if ids:
        observed_ids = set(ids)
        minimum = min(observed_ids)
        maximum = max(observed_ids)
        internal_gaps = [
            value
            for value in range(minimum + 1, maximum)
            if value not in observed_ids
        ]
        distance_limit = max(1, query_count * 4)
        for miss_index in range(miss_count):
            miss_kind = miss_index % 3
            if miss_kind == 0:
                misses.append(minimum - 1 - random.randrange(distance_limit))
            elif miss_kind == 1 and internal_gaps:
                misses.append(random.choice(internal_gaps))
            else:
                misses.append(maximum + 1 + random.randrange(distance_limit))
    else:
        # There is no observed range to bracket. Any integer is absent, so use
        # a deterministic signed range instead of pretending it is a hit.
        misses = [
            random.randrange(-max(1, query_count * 4), max(2, query_count * 4))
            for _ in range(miss_count)
        ]

    queries = hits + misses
    random.shuffle(queries)
    return ids, queries
