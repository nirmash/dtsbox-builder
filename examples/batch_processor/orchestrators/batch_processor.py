import dtsbox
from durabletask import task


@dtsbox.orchestrator
def batch_processor(ctx: task.OrchestrationContext, groups: list[list[int]]):
    """Parent: dispatches one child orchestrator per group, aggregates results."""
    child_results = []
    for idx, group in enumerate(groups):
        result = yield ctx.call_sub_orchestrator(
            "square_group",
            input={"group_id": idx, "numbers": group},
        )
        child_results.append(result)
    return child_results


@dtsbox.orchestrator
def square_group(ctx: task.OrchestrationContext, payload: dict):
    """Child: fan-out over the group's numbers and square each."""
    group_id = payload["group_id"]
    numbers = payload["numbers"]
    tasks = [ctx.call_activity("square_one", input=n) for n in numbers]
    squared = yield task.when_all(tasks)
    stdouts = [int(r["stdout"]) for r in squared]
    return {"group_id": group_id, "results": stdouts}
