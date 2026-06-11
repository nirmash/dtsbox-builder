"""Step 2: adds 10 to the previous step's result.

Later steps receive the previous step's full dict — unwrap via input_data["stdout"].
Currently a SMOKE-TEST STUB.
"""
import dtsbox


@dtsbox.activity
def add_ten(ctx, input_data):
    # SMOKE-TEST STUB — unwraps previous step's stdout, mimics run_sandbox_step shape.
    n = int(input_data["stdout"])
    return {"stdout": str(n + 10), "sandbox_id": "local-smoke", "elapsed_seconds": 0.0}


# Real Azure version:
#
# @dtsbox.activity
# def add_ten(ctx, input_data):
#     n = int(input_data["stdout"])
#     return dtsbox.run_sandbox_step(
#         ctx,
#         source="python-3.12",
#         files={"/tmp/work.py": f"print({n} + 10)"},
#         command="python3 /tmp/work.py",
#         workflow="process_pipeline",
#     )
