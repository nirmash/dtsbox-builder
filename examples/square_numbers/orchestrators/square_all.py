"""Fan-out orchestrator: schedules one activity per input integer, collects squares.

Deterministic — DTS replays this function from history on any crash or restart.
Never call time.now(), random(), or do I/O here; use activities for side effects.
"""
import dtsbox
from durabletask import task


@dtsbox.orchestrator
def square_all(ctx, numbers: list):
    # Schedule one activity task per integer. No work runs yet — these are declarations.
    tasks = [ctx.call_activity("square_one", input=n) for n in numbers]

    # Checkpoint: orchestrator suspends. DTS dispatches all tasks. On resume, results is populated.
    results = yield task.when_all(tasks)

    # Aggregate branch outputs into the final result.
    return {"processed": len(results), "results": results}
