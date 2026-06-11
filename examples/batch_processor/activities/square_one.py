import dtsbox
from durabletask import task


@dtsbox.activity
def square_one(ctx: task.ActivityContext, n: int) -> dict:
    """Local smoke stub — squares the input. Real version below uses run_sandbox_step."""
    return {"stdout": str(n * n), "sandbox_id": "local-smoke", "elapsed_seconds": 0.0}


# Real Azure version (uncomment after `dtsbox setup` + comment out the stub above):
# @dtsbox.activity
# def square_one(ctx: task.ActivityContext, n: int) -> dict:
#     return dtsbox.run_sandbox_step(
#         image="python:3.12-slim",
#         command=["python", "-c", f"print({n}**2)"],
#     )
