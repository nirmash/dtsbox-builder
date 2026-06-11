"""Chaining orchestrator: each step's output feeds the next.

Deterministic — DTS replays this from history on every crash. Each step's result is recorded
in history, so on resume completed steps return cached values and only the next pending step runs.
"""
import dtsbox


@dtsbox.orchestrator
def process_pipeline(ctx, payload):
    # Step 1 — receives the initial workflow payload
    result_1 = yield ctx.call_activity("double_it", input=payload)

    # Step 2 — receives step 1's output (full dict; unwrap via input_data["stdout"] in the activity)
    result_2 = yield ctx.call_activity("add_ten", input=result_1)

    # Step 3 — receives step 2's output
    result_3 = yield ctx.call_activity("format_report", input=result_2)

    return {"step_1": result_1, "step_2": result_2, "step_3": result_3}
