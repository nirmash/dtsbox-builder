"""Step 1: doubles the input number.

First step receives the raw workflow input (here, an integer). Currently a SMOKE-TEST STUB.
"""
import dtsbox


@dtsbox.activity
def double_it(ctx, input_data):
    # SMOKE-TEST STUB — same return shape as run_sandbox_step.
    n = int(input_data)
    return {"stdout": str(n * 2), "sandbox_id": "local-smoke", "elapsed_seconds": 0.0}


# Real Azure version:
#
# @dtsbox.activity
# def double_it(ctx, input_data):
#     return dtsbox.run_sandbox_step(
#         ctx,
#         source="python-3.12",
#         files={"/tmp/work.py": f"print({int(input_data)} * 2)"},
#         command="python3 /tmp/work.py",
#         workflow="process_pipeline",
#     )
