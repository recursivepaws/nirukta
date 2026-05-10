import sys
import traceback
import dill as pickle
from pathlib import Path
from typing import Any, Callable

from janim.logger import log

_RECURSION_LIMIT = 10_000

CACHE_VERSION = 1


def build_cached(cache: dict, key: str, builder: Callable, label: str = "") -> Any:
    tag = f" ({label})" if label else ""

    if key in cache:
        log.info(f"Reusing from memory: {tag}")
        return cache[key]

    cache_file = _cache_path(key)
    if cache_file.exists():
        try:
            with open(cache_file, "rb") as f:
                old_limit = sys.getrecursionlimit()
                sys.setrecursionlimit(_RECURSION_LIMIT)
                try:
                    built = pickle.load(f)
                finally:
                    sys.setrecursionlimit(old_limit)
            cache[key] = built
            log.info(f"Reusing from disk: {tag}")
            return built
        except Exception as e:
            log.warning(f"Disk cache load failed{tag}: {e}\n{traceback.format_exc()}")
            cache_file.unlink(missing_ok=True)

    built = builder()
    cache[key] = built

    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "wb") as f:
            old_limit = sys.getrecursionlimit()
            sys.setrecursionlimit(_RECURSION_LIMIT)
            try:
                pickle.dump(built, f)
            finally:
                sys.setrecursionlimit(old_limit)
        log.info(f"Saved to disk: {tag}")
    except Exception as e:
        log.warning(f"Disk cache write failed{tag}: {e}")
        cache_file.unlink(missing_ok=True)

    return built


def _cache_path(key: str) -> Path:
    return Path(__file__).parent.parent / ".cache" / f"v{CACHE_VERSION}" / f"{key}.pkl"
