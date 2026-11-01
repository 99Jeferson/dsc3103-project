import json
from types import SimpleNamespace

from src.stream import consumer


def test_consume_deduplicates_routes_late_events_and_finalises_windows(
    tmp_path, monkeypatch, capsys
):
    broker = tmp_path / "events.jsonl"
    late_log = tmp_path / "late_events.jsonl"
    duplicate_log = tmp_path / "duplicate_events.jsonl"
    events = [
        {
            "event_id": "e1",
            "event_time": 985,
            "market": "Central",
            "commodity": "Maize",
            "price": 2.0,
        },
        {
            "event_id": "e1",
            "event_time": 985,
            "market": "Central",
            "commodity": "Maize",
            "price": 2.0,
        },
        {
            "event_id": "e2",
            "event_time": 965,
            "market": "Central",
            "commodity": "Beans",
            "price": 4.0,
        },
    ]
    broker.write_text("".join(json.dumps(event) + "\n" for event in events))

    clock = [1000.0]
    monkeypatch.setattr(
        consumer,
        "time",
        SimpleNamespace(
            time=lambda: clock[0],
            sleep=lambda duration: clock.__setitem__(0, clock[0] + duration),
        ),
    )
    monkeypatch.setattr(consumer, "BROKER", str(broker))
    monkeypatch.setattr(consumer, "LATE_LOG", str(late_log))
    monkeypatch.setattr(consumer, "DUP_LOG", str(duplicate_log))
    monkeypatch.setattr(consumer, "WINDOW", 10)
    monkeypatch.setattr(consumer, "WATERMARK", 20)
    monkeypatch.setattr(consumer, "IDLE_STOP", 11)

    consumer.consume()

    assert capsys.readouterr().out.splitlines() == [
        "Window 980: count=1, mean_price=2.00",
        (
            "Consumer idle, stopping. Late: 1 | Accepted within watermark: 1 "
            "| Duplicates: 1"
        ),
    ]
    assert [json.loads(line)["event_id"] for line in late_log.read_text().splitlines()] == [
        "e2"
    ]
    assert json.loads(late_log.read_text())["reason"] == "watermark passed"
    assert [
        json.loads(line)["event_id"] for line in duplicate_log.read_text().splitlines()
    ] == ["e1"]
