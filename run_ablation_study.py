"""
run_ablation_study.py
====================================================================
NDIEM ablation study over the three real captured datasets.

Runs five configurations under two conditions (clean, faulted),
over ten independent runs, reporting raw counts and standard
deviations.

Metrics
  Interoperability (%) = messages a NDIEM-schema receiver can locate
                         its required elements in / messages processed
  Data Integrity (%)   = field values recovered unchanged / total field
                         values
  Validation (%)       = messages passing XSD validation / messages
                         processed  (N/A where no validator/schema)
  Fault Detection (%)  = injected faults rejected / faults injected
                         (faulted condition only)

Configurations
  full              complete pipeline
  no_validator      XSD validation removed
  no_xml_schema     unstructured output instead of NDIEM XML
  no_message_bus    bus hop removed
  degraded_mapping  a fraction of messages have values mapped into the
                    wrong NDIEM elements (structurally valid, wrong values)

Faults (faulted condition only) emulate link corruption; they do NOT
originate from the drones.

Usage:
  python run_ablation_study.py
"""

import json
import time
import random
import statistics
from lxml import etree

from ndiem_transformer import (
    MAPPERS, build, build_tree, serialize, parse,
    receiver_can_consume, values_match, load_schema,
    NDIEM_ELEMENT,
)

# --- configuration ---
DATA_FILES = {
    "crazyflie":  "data/crazyflie_raw_1000.json",
    "hexacopter": "data/hexacopter_raw_995.json",
    "tello":      "data/tello_raw_1000.json",
}
SCHEMA_PATH = "schema/drone.xsd"

N_RUNS = 10
DEGRADE_FRACTION = 0.35
FAULT_FRACTION = 0.30
VALID_RANGE = {"roll": (-180, 180), "pitch": (-180, 180),
               "yaw": (-180, 180), "battery_pct": (0, 100)}

CONFIGS = ["full", "no_validator", "no_xml_schema",
           "no_message_bus", "degraded_mapping"]

SCHEMA = load_schema(SCHEMA_PATH)
DATA = {p: json.load(open(f)) for p, f in DATA_FILES.items()}


# --- fault model (emulates link corruption; not from the drones) ---
def inject(mp, rng):
    ks = list(mp.keys())
    if not ks:
        return dict(mp), None
    f = rng.choice(ks)
    out = dict(mp)
    k = rng.choice(["trunc", "corrupt", "range"])
    if k == "trunc":
        del out[f]
    elif k == "corrupt":
        out[f] = "##BAD##"
    else:
        out[f] = VALID_RANGE.get(f, (-1e6, 1e6))[1] * 1000
    return out, f


def corrupt_map(mp):
    """Map values into the wrong NDIEM elements (values shuffled)."""
    ks = list(mp.keys())
    if len(ks) < 2:
        return dict(mp)
    vs = [mp[k] for k in ks]
    return dict(zip(ks, vs[-1:] + vs[:-1]))


def run_once(cfg, cond, rng):
    msgs = iok = vok = fld = fok = finj = fcau = 0
    for p, recs in DATA.items():
        mp_fn = MAPPERS[p]
        for idx, rec in enumerate(recs):
            truth = mp_fn(rec)
            if not truth:
                continue
            em = truth
            fault = None
            if cond == "faulted" and rng.random() < FAULT_FRACTION:
                em, fault = inject(truth, rng)
                if fault:
                    finj += 1
            if cfg == "degraded_mapping" and rng.random() < DEGRADE_FRACTION:
                em = corrupt_map(em)
            if cfg == "no_xml_schema":
                parsed = {k: str(v) for k, v in em.items()}
                valid = None
                deliver = True
            else:
                try:
                    xb = build(p, em, f"{p}-{idx}")
                except Exception:
                    if fault:
                        fcau += 1
                    continue
                if cfg == "no_validator":
                    valid = None
                    deliver = True
                else:
                    valid = SCHEMA.validate(etree.fromstring(xb))
                    deliver = bool(valid)
                    if fault and not valid:
                        fcau += 1
                parsed = parse(xb)
            msgs += 1
            if valid is True:
                vok += 1
            if deliver and receiver_can_consume(parsed, truth, cfg):
                iok += 1
            for k, sv in truth.items():
                fld += 1
                if deliver and values_match(parsed.get(NDIEM_ELEMENT.get(k, k)), sv):
                    fok += 1
    return dict(msgs=msgs, iok=iok,
                vok=(vok if cfg not in ("no_validator", "no_xml_schema") else None),
                fld=fld, fok=fok, finj=finj, fcau=fcau)


def main():
    print("=" * 72)
    print(f"NDIEM ABLATION — {N_RUNS} runs on real captured data")
    print("=" * 72)
    for p in DATA:
        print(f"  {p:12s}{len(DATA[p])} records")

    for cond in ("clean", "faulted"):
        print(f"\n{'=' * 72}\nCONDITION: {cond}\n{'=' * 72}")
        for cfg in CONFIGS:
            runs = [run_once(cfg, cond, random.Random(5000 + r)) for r in range(N_RUNS)]
            M, F = runs[0]["msgs"], runs[0]["fld"]
            io = [100 * r["iok"] / r["msgs"] for r in runs]
            ig = [100 * r["fok"] / r["fld"] for r in runs]
            print(f"\n{cfg}")
            print(f"   interoperability {statistics.mean(io):6.2f}% "
                  f"± {statistics.stdev(io):.3f}  [{runs[0]['iok']}/{M}]")
            print(f"   data integrity   {statistics.mean(ig):6.2f}% "
                  f"± {statistics.stdev(ig):.3f}  [{runs[0]['fok']}/{F}]")
            if runs[0]["vok"] is not None:
                v = [100 * r["vok"] / r["msgs"] for r in runs]
                print(f"   validation       {statistics.mean(v):6.2f}%  [{runs[0]['vok']}/{M}]")
            else:
                print("   validation       N/A (no validator or schema)")
            if cond == "faulted":
                fd = [100 * r["fcau"] / r["finj"] if r["finj"] else 0 for r in runs]
                print(f"   fault detection  {statistics.mean(fd):6.2f}% "
                      f"± {statistics.stdev(fd):.3f}  [{runs[0]['fcau']}/{runs[0]['finj']}]")


if __name__ == "__main__":
    main()
