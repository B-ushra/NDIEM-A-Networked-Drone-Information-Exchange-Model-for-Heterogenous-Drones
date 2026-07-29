"""
run_latency_study.py
====================================================================
Per-platform latency and message-size measurement.

  Transformation latency = build_tree only        (Table 6)
  End-to-End time         = build_tree + serialize + validate  (Table 4)
  Overhead                = end-to-end minus transformation

Both stages are timed in a single pass so that end-to-end is always
>= transformation by construction. Message sizes compare the native
record with the serialized NDIEM message.

Usage:
  python run_latency_study.py
"""

import json
import time
import statistics
from lxml import etree

from ndiem_transformer import MAPPERS, build, build_tree, serialize, load_schema

DATA_FILES = {
    "crazyflie":  "data/crazyflie_raw_1000.json",
    "hexacopter": "data/hexacopter_raw_995.json",
    "tello":      "data/tello_raw_1000.json",
}
SCHEMA_PATH = "schema/drone.xsd"
RUNS = 5

SCHEMA = load_schema(SCHEMA_PATH)
DATA = {p: json.load(open(f)) for p, f in DATA_FILES.items()}


def main():
    print("=" * 78)
    print("LATENCY AND MESSAGE SIZE")
    print("=" * 78)
    print(f"{'platform':<12}{'N':>6}{'transform_ms':>14}{'sd':>9}"
          f"{'end2end_ms':>13}{'sd':>9}{'overhead':>10}"
          f"{'ndiem_B':>9}{'native_B':>10}")
    print("-" * 92)

    for p, recs in DATA.items():
        tr_r, e2e_r = [], []
        for _ in range(RUNS):
            tr, e2e = [], []
            for i, rec in enumerate(recs):
                mp = MAPPERS[p](rec)
                if not mp:
                    continue
                t0 = time.perf_counter()
                tree = build_tree(p, mp, f"{p}-{i}")     # transformation only
                t1 = time.perf_counter()                 # Table 6 stops here
                xb = serialize(tree)                     # serialization
                SCHEMA.validate(tree)                    # validation
                t2 = time.perf_counter()                 # Table 4 stops here
                tr.append((t1 - t0) * 1000)
                e2e.append((t2 - t0) * 1000)
            tr_r.append(statistics.mean(tr))
            e2e_r.append(statistics.mean(e2e))

        sizes, native, n = [], [], 0
        for i, rec in enumerate(recs):
            mp = MAPPERS[p](rec)
            if not mp:
                continue
            n += 1
            sizes.append(len(build(p, mp, f"{p}-{i}")))
            native.append(len(json.dumps(rec["telemetry"], separators=(",", ":"))))

        tm = statistics.mean(tr_r)
        em = statistics.mean(e2e_r)
        print(f"{p:<12}{n:>6}{tm:>14.4f}{statistics.stdev(tr_r):>9.4f}"
              f"{em:>13.4f}{statistics.stdev(e2e_r):>9.4f}{em - tm:>10.4f}"
              f"{statistics.mean(sizes):>9.0f}{statistics.mean(native):>10.0f}")


if __name__ == "__main__":
    main()
