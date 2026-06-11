"""Step 3: formats the previous step's result as a string.

Final step in the chain. Currently a SMOKE-TEST STUB.
"""
import dtsbox


@dtsbox.activity
def format_report(ctx, input_data):
    # SMOKE-TEST STUB.
    n = int(input_data["stdout"])
    return {"stdout": f"Final: {n}", "sandbox_id": "local-smoke", "elapsed_seconds": 0.0}


# Real Azure version:
#
# @dtsbox.activity
# def format_report(ctx, input_data):
#     n = int(input_data["stdout"])
#     return dtsbox.run_sandbox_step(
#         ctx,
#         source="python-3.12",
#         files={"/tmp/work.py": f"print('Final: {n}')"},
#         command="python3 /tmp/work.py",
#         workflow="process_pipeline",
#     )
