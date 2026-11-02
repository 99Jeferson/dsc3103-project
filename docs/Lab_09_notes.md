# Lab 09 notes — Streaming and event-driven data systems

## Step 1 — Late and duplicate events

The producer creates late events with `delay = random.uniform(15, 40)` and sets `event_time` to `now - delay`. It writes a duplicate when the later `random.random() < 0.05` condition is true.

An event can arrive after the time it describes because it was delayed in transit or buffered before delivery. For example, a market-price sensor may lose network connectivity and upload its locally buffered readings after it reconnects.

## Step 3 — Window output timing

A window does not print as soon as its 10-second event-time interval ends. The consumer waits until the window end plus the watermark, so with `WATERMARK = 20` it prints about 20 seconds after the window ends (about 30 seconds after the window starts). The 0.2-second polling interval can add a small amount of extra delay. `WATERMARK` controls the wait.

## Step 4 — Event time versus processing time

In the 20-second-watermark run, late events had event-time window starts `1793483190`, `1793483200`, `1793483210`, and `1793483220` (4, 4, 10, and 64 events, respectively). Using receipt time instead would move delayed readings out of those earlier event-time windows and into later processing-time windows. In this run the later printed windows started at `1793483230`, `1793483240`, `1793483250`, and `1793483260`; collectively, these later windows would receive more readings while the earlier event-time windows would have smaller counts.

The consumer does not persist a receipt timestamp, so its output cannot identify the exact later window for each late record. The window starts above are the affected event-time windows from this run; the random producer means the exact windows change on another run.

## Step 5 — Watermarks

In one run of 300 unique events, the consumer caught 18 duplicates. The late-event and accepted-late counts below are from three consumers reading the same stream. “Accepted within watermark” counts events processed after their event-time window ended but before its watermark expired. Counts vary between runs because event delays and duplicates are random.

| WATERMARK | Late events logged | Delay before a window prints |
|---:|---:|---:|
| 5 | 155 | About 5 seconds after the window ends |
| 20 | 82 | About 20 seconds after the window ends |
| 40 | 8 | About 40 seconds after the window ends |

Accepted after the event-time window ended but still inside the watermark: 67 (watermark 5), 140 (watermark 20), and 214 (watermark 40).

In the later verification run, the producer was run to completion before the consumer was started. The broker contained 313 lines (300 unique event IDs and 13 injected duplicates). Because the consumer started after the events had aged beyond the 20-second watermark, it routed all 300 unique events to `late_events.jsonl`, accepted 0 within the watermark, and caught all 13 duplicates. This is a useful demonstration of why the consumer should be started while the producer is still running; those sequential-run counts are not the expected results of a concurrent stream run.

For a fraud alert, I would choose a short watermark such as 5 seconds so alerts arrive sooner, and handle very late records separately. For a daily price report, I would choose a longer watermark such as 40 seconds because completeness matters more than a few seconds of latency. With `IDLE_STOP = 45`, the consumer can stop before the newest window is finalised when the watermark is 40 seconds: a full window plus its watermark can take 50 seconds. A production consumer should allow pending windows to finalise before shutting down.

## Step 6 — Duplicates and state

The first measured run caught 18 duplicate lines, and the later sequential verification run caught 13. Without the `seen_ids` check, each duplicate would be counted again, inflating the count and price total for its window. The number varies because the producer injects duplicates randomly.

`seen_ids` uses memory proportional to the number of unique event IDs. At 10 million events per day, retaining every ID indefinitely would keep consuming more memory. One option is to expire IDs after a retention period. The trade-off is that a duplicate arriving after its ID expires can be counted again. A Bloom filter uses less memory but can incorrectly classify a new ID as a duplicate.

## Step 7 — Restarting the consumer

`offset`, `windows`, `finalised`, and `seen_ids` exist only in process memory. Stopping the consumer loses all four. On restart, `offset` returns to zero, so the consumer reads the broker from the beginning and can count already-processed events again; its per-run late and duplicate logs are also reset.

To resume correctly, checkpoint the broker offset, window counts and totals, finalised-window state, and deduplication IDs (or their retained time range). The checkpoint and offset need to be saved consistently so a restart neither skips nor double-counts events.

## Step 8 — Architecture

See [stream_architecture.png](./stream_architecture.png). Late records leave the consumer for the late-event log, and repeated event IDs are caught by the consumer before they can change a window.

## Batch versus streaming

A five-minute batch job would be sufficient for periodic price summaries, dashboards refreshed every few minutes, and data that can tolerate delayed corrections. It is simpler to operate and can recompute aggregates from stored records.

Streaming is appropriate when a price spike or suspicious transaction needs to trigger an alert quickly, when downstream systems need continuously updated metrics, or when waiting five minutes could miss a time-sensitive response. Late-event handling and deduplication are still needed because live delivery can be delayed or repeated.
