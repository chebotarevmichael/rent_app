import hashlib
from datetime import datetime, timezone

import ulid

from collections import defaultdict
from collections.abc import Iterable


def group_list_by_key(items: Iterable, key: str) -> dict[str, list]:
    _key2item = defaultdict(list)
    for item in items:
        _key2item[getattr(item, key)].append(item)
    return _key2item


def group_set_by_key(items: Iterable, key: str) -> dict[str, set]:
    _key2item = defaultdict(set)
    for item in items:
        _key2item[getattr(item, key)].add(item)
    return _key2item


def int_hash(*args) -> int:
    s = ';'.join(map(str, args))
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "big")


def gen_id() -> str:
    return ulid.new()   # 01HZXQ1M0P6J1Q4WG9T79E9G6N


def is_same_utc_day(ts: datetime) -> bool:
    now = datetime.now(timezone.utc)
    return ts.date() == now.date()