"""
clean_capture_log.py
====================================================================
Extracts clean telemetry JSON from a messy capture console log.

A capture session prints log lines, progress markers and sometimes
tracebacks to the screen. This tool reads such a log and recovers only
the telemetry dictionaries, writing a clean .json file the evaluation
pipeline can read.

It handles two common shapes:

  1. progress lines like
        [42/1000] {"pitch": 3, "roll": -7, ...}
  2. pretty-printed JSON records containing a "telemetry" object

Lines that are log messages, warnings or tracebacks are ignored.

USAGE
    python clean_capture_log.py  input_log.txt  output.json  --platform tello

The --platform tag is stored on each record so the pipeline knows the
message_type.
"""

import re
import sys
import json
import argparse

PLATFORM_MSGTYPE = {
    "crazyflie":  "CRAZYFLIE_TELEMETRY",
    "hexacopter": "MAVLINK",
    "tello":      "TELLO_STATE",
}


def extract_progress_dicts(text):
    """Find `[n/N] { ... }` lines and parse the dict after the marker."""
    records = []
    # matches [12/1000] {....}  where the dict is on the same line
    pattern = re.compile(r'\[\d+\s*/\s*\d+\]\s*(\{.*?\})\s*$', re.MULTILINE)
    for m in pattern.finditer(text):
        blob = m.group(1)
        try:
            # progress lines print with json.dumps, so JSON parses directly;
            # fall back to python-literal style if needed
            try:
                d = json.loads(blob)
            except json.JSONDecodeError:
                d = json.loads(blob.replace("'", '"'))
            records.append(d)
        except Exception:
            continue
    return records


def extract_pretty_records(text):
    """Find balanced { ... } blocks that contain a telemetry object."""
    records = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    blob = text[start:i + 1]
                    if '"telemetry"' in blob or 'telemetry' in blob:
                        try:
                            records.append(json.loads(blob))
                        except Exception:
                            pass
                    start = None
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--platform", required=True,
                    choices=list(PLATFORM_MSGTYPE))
    args = ap.parse_args()

    text = open(args.input, "r", encoding="utf-8", errors="ignore").read()

    dicts = extract_progress_dicts(text)
    source = "progress lines"
    if not dicts:
        dicts = extract_pretty_records(text)
        source = "pretty-printed records"

    if not dicts:
        print("No telemetry found. Is this the right log, and did the "
              "capture actually print records?")
        sys.exit(1)

    msgtype = PLATFORM_MSGTYPE[args.platform]
    records = []
    for i, d in enumerate(dicts):
        telemetry = d.get("telemetry", d)   # progress lines are the dict itself
        records.append({
            "capture_time": d.get("capture_time"),
            "message_type": d.get("message_type", msgtype),
            "telemetry": telemetry,
        })

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"Recovered {len(records)} records from {source}.")
    print(f"Written to {args.output}")
    print(f"First record fields: {list(records[0]['telemetry'].keys())}")


if __name__ == "__main__":
    main()
