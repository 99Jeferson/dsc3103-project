import json
import time

BROKER = "data/stream/events.jsonl"
LATE_LOG = "data/stream/late_events.jsonl"
DUP_LOG = "data/stream/duplicate_events.jsonl"

WINDOW = 10
WATERMARK = 20
IDLE_STOP = 45


def window_start(event_time):
    return int(event_time // WINDOW) * WINDOW


def append(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def consume():
    for path in (LATE_LOG, DUP_LOG):
        open(path, "w").close()

    offset = 0
    windows = {}
    finalised = set()
    seen_ids = set()
    accepted_late_count = 0
    last_new = time.time()

    while time.time() - last_new < IDLE_STOP:
        with open(BROKER) as f:
            lines = f.readlines()
        new_lines = lines[offset:]
        offset = len(lines)
        if new_lines:
            last_new = time.time()

        for line in new_lines:
            event = json.loads(line)
            now = time.time()

            if event["event_id"] in seen_ids:
                append(DUP_LOG, event)
                continue
            seen_ids.add(event["event_id"])

            ws = window_start(event["event_time"])
            if ws in finalised:
                append(LATE_LOG, {**event, "reason": "window already finalised"})
                continue
            if now >= ws + WINDOW + WATERMARK:
                append(LATE_LOG, {**event, "reason": "watermark passed"})
                continue

            if now >= ws + WINDOW:
                accepted_late_count += 1

            window = windows.setdefault(ws, {"n": 0, "total": 0.0})
            window["n"] += 1
            window["total"] += event["price"]

        now = time.time()
        for ws in sorted(windows):
            if ws not in finalised and now >= ws + WINDOW + WATERMARK:
                window = windows[ws]
                mean = window["total"] / window["n"]
                print(
                    f"Window {ws}: count={window['n']}, "
                    f"mean_price={mean:.2f}"
                )
                finalised.add(ws)

        time.sleep(0.2)

    with open(LATE_LOG) as late_log:
        late_count = sum(1 for _ in late_log)
    with open(DUP_LOG) as duplicate_log:
        duplicate_count = sum(1 for _ in duplicate_log)
    print(
        "Consumer idle, stopping. Late:",
        late_count,
        "| Accepted within watermark:",
        accepted_late_count,
        "| Duplicates:",
        duplicate_count,
    )


if __name__ == "__main__":
    consume()
