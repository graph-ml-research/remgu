"""A tiny, runnable example of recording an experiment with ReMgu.

Run from the repository root with: python examples/hello_remgu.py
"""
import time

from remgu import Experiment, Motivation

experiment = Experiment("hello-remgu")
with experiment.run(
    hypothesis="The example loss decreases over five steps",
    motivation=Motivation(type="new"),
) as run:
    run.log_params({"learning_rate": 0.01, "steps": 5})
    for step in range(5):
        time.sleep(0.1)  # Stand in for a small amount of training work.
        loss = 1.0 / (step + 1)
        run.log_metric("loss", loss, step=step)
        print(f"step={step} loss={loss:.3f}")

print(f"Done. Open {run.path} to inspect the saved files.")
