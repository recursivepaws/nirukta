import cProfile
import pstats
import time

with open("./blueprints/sUtrARi/SrIsarasvatIstotraM.sutra") as f:
    source = f.read()

# --- parsing / logic stage ---
t0 = time.perf_counter()
from parser import parse_sutra  # noqa: E402

sutra = parse_sutra(source)
t1 = time.perf_counter()
print(f"parse: {t1 - t0:.2f}s")

# --- janim build stage ---
from nirukta import Nirukta  # noqa: E402

with cProfile.Profile() as pr:
    tl = Nirukta(sutra)
    built = tl.build()
t2 = time.perf_counter()
print(f"build: {t2 - t1:.2f}s")

stats = pstats.Stats(pr)
stats.sort_stats(pstats.SortKey.CUMULATIVE)
stats.print_stats(30)
