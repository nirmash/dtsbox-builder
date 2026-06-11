"""Fan-out activity: squares one integer per scheduled task.

Currently configured as a SMOKE-TEST STUB so the example runs locally against the DTS emulator
without Azure. To use real Azure sandboxes, replace the function body with the commented version
below, then run `dtsbox setup` + `dtsbox publish`.
"""
import dtsbox


@dtsbox.activity
def square_one(ctx, item):
    # SMOKE-TEST STUB — returns the same dict shape run_sandbox_step would.
    n = int(item)
    return {"stdout": str(n * n), "sandbox_id": "local-smoke", "elapsed_seconds": 0.0}


# Real Azure version (uncomment, delete the stub above):
#
# @dtsbox.activity
# def square_one(ctx, item):
#     return dtsbox.run_sandbox_step(
#         ctx,
#         source="python-3.12",
#         files={"/tmp/work.py": f"print({item} * {item})"},
#         command="python3 /tmp/work.py",
#         workflow="square_all",
#     )
