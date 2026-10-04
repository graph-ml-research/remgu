# -*- coding: utf8 -*-
from __future__ import annotations

import argparse
from typing import Sequence

from .consistency import check_consistency
from .models import Execution, Motivation, ResearchMetadata, Review
from .run import Run
from .storage import FileStorage

__author__ = 'Mstislav Maslennikov'



def _build_run(storage: FileStorage, run_id: str) -> Run:
    data = storage.read_run(run_id)
    if not data:
        raise SystemExit(f"Run not found: {run_id}")
    try:
        research_data = data["research"]
        motivation_data = research_data["motivation"]
        execution_data = data["execution"]
        review_data = data["review"]
        motivation = Motivation(
            type=str(motivation_data["type"]),
            reference=motivation_data.get("reference"),
        )
        from datetime import datetime
        def parse_time(value):
            if value is None:
                return None
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        execution = Execution(
            status=str(execution_data["status"]),
            started_at=parse_time(execution_data.get("started_at")),
            finished_at=parse_time(execution_data.get("finished_at")),
            error=execution_data.get("error"),
        )
        review = Review(
            status=str(review_data.get("status", "needs_review")),
            conclusion=review_data.get("conclusion"),
            next_step=review_data.get("next_step"),
        )
        return Run(
            run_id=run_id,
            research=ResearchMetadata(
                hypothesis=str(research_data["hypothesis"]),
                motivation=motivation,
            ),
            storage=storage,
            path=storage.run_path(run_id),
            execution=execution,
            review=review,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"Invalid run.yaml for {run_id}: {exc}") from exc


def cmd_new(args: argparse.Namespace) -> int:
    storage = FileStorage(args.base_path)
    storage.initialize()
    if storage.get_active() is not None:
        raise SystemExit(f"Another run is already active: {storage.get_active()}")
    run_id = storage.next_run_id()
    motivation = Motivation(type=args.motivation_type, reference=args.reference)
    run = Run(
        run_id=run_id,
        research=ResearchMetadata(hypothesis=args.hypothesis, motivation=motivation),
        storage=storage,
        path=storage.run_path(run_id),
        execution=Execution(status="running"),
        review=Review(),
    )
    storage.set_active(run_id)
    run.start()
    print(run_id)
    return 0


def cmd_finish(args: argparse.Namespace) -> int:
    storage = FileStorage(args.base_path)
    run_id = args.run_id or storage.get_active()
    if run_id is None:
        raise SystemExit("No run specified and no active run exists")
    run = _build_run(storage, run_id)
    if run.execution.status != "completed":
        raise SystemExit("Research review is available only after a completed execution")
    if run.review.status == "reviewed":
        raise SystemExit(f"Run is already reviewed: {run_id}")
    if not args.conclusion:
        raise SystemExit("--conclusion is required")
    if not args.next_step:
        raise SystemExit("--next-step is required")
    run.review.conclusion = args.conclusion
    run.review.next_step = args.next_step
    run.review.status = "reviewed"
    run.save()
    print(run_id)
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    storage = FileStorage(args.base_path)
    run_id = args.run_id or storage.get_active()
    if run_id is None:
        raise SystemExit("No run specified and no active run exists")
    run = _build_run(storage, run_id)
    if run.execution.status != "running":
        raise SystemExit(f"Only a running run can be resumed: {run_id} ({run.execution.status})")
    active = storage.get_active()
    if active is None:
        storage.set_active(run_id)
    elif active != run_id:
        raise SystemExit(f"Another run is already active: {active}")
    print(run_id)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    storage = FileStorage(args.base_path)
    report = check_consistency(storage)

    print(f"completed runs: {len(report.completed_runs)}")
    print(f"runs with hypotheses: {len(report.runs_with_hypotheses)}")
    if report.issues:
        print("issues:")
        for issue in report.issues:
            print(f"  {issue.severity}: {issue.run_id}: {issue.code}: {issue.message}")
    else:
        print("issues: none")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    storage = FileStorage(args.base_path)
    active = storage.get_active()
    if active is None:
        print("active: none")
        return 0
    run = _build_run(storage, active)
    print(f"run_id: {run.run_id}")
    print(f"execution.status: {run.execution.status}")
    print(f"review.status: {run.review.status}")
    return 0


def cmd_previous(args: argparse.Namespace) -> int:
    storage = FileStorage(args.base_path)
    run_ids = storage.list_run_ids()[-args.limit:]
    if not run_ids:
        print("runs: none")
        return 0

    for run_id in run_ids:
        run = _build_run(storage, run_id)
        motivation = run.research.motivation
        reference = f" -> {motivation.reference}" if motivation.reference else ""
        hypothesis = " ".join(run.research.hypothesis.split())
        print(
            f"{run.run_id} | "
            f"execution={run.execution.status} | "
            f"review={run.review.status} | "
            f"motivation={motivation.type}{reference} | "
            f"hypothesis={hypothesis}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research")
    parser.add_argument("--base-path", default=".research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new = subparsers.add_parser("new")
    new.add_argument("--hypothesis", required=True)
    new.add_argument("--motivation-type", default="new")
    new.add_argument("--reference")
    new.set_defaults(func=cmd_new)

    finish = subparsers.add_parser("finish")
    finish.add_argument("run_id", nargs="?")
    finish.add_argument("--conclusion")
    finish.add_argument("--next-step")
    finish.set_defaults(func=cmd_finish)

    resume = subparsers.add_parser("resume")
    resume.add_argument("run_id", nargs="?")
    resume.set_defaults(func=cmd_resume)

    status = subparsers.add_parser("status")
    status.set_defaults(func=cmd_status)

    check = subparsers.add_parser("check")
    check.set_defaults(func=cmd_check)

    previous = subparsers.add_parser("previous")
    previous.add_argument("--limit", type=int, default=5)
    previous.set_defaults(func=cmd_previous)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
