# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Command-line interface for ReMgu research lifecycle operations."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Sequence

from remgu.consistency.consistency_report import ConsistencyReport
from remgu.models.execution import Execution
from remgu.models.motivation import Motivation
from remgu.consistency.research_checker import ResearchChecker
from remgu.models.research_metadata import ResearchMetadata
from remgu.models.review import Review
from remgu.run import Run
from remgu.file_storage import FileStorage


class ResearchCli:
    """Own the argument parser and command handlers for the ``research`` CLI."""

    def __init__(self) -> None:
        """Create the CLI parser and register all supported commands."""
        self.parser = self._build_parser()
        """Argument parser used by the CLI entry point."""

    def main(self, argv: Sequence[str] | None = None) -> int:
        """Parse arguments and execute the selected command.

        Args:
            argv: Optional command-line arguments without the executable name.
        """
        args = self.parser.parse_args(argv)
        return args.func(args)

    def _build_parser(self) -> argparse.ArgumentParser:
        """Construct the complete ``research`` command parser."""
        parser = argparse.ArgumentParser(prog="research")
        parser.add_argument("--base-path", default=".research")
        subparsers = parser.add_subparsers(dest="command", required=True)
        new = subparsers.add_parser("new")
        new.add_argument("--hypothesis", required=True)
        new.add_argument("--motivation-type", default="new")
        new.add_argument("--reference")
        new.set_defaults(func=self._cmd_new)
        finish = subparsers.add_parser("finish")
        finish.add_argument("run_id", nargs="?")
        finish.add_argument("--conclusion")
        finish.add_argument("--next-step")
        finish.set_defaults(func=self._cmd_finish)
        resume = subparsers.add_parser("resume")
        resume.add_argument("run_id", nargs="?")
        resume.set_defaults(func=self._cmd_resume)
        status = subparsers.add_parser("status")
        status.set_defaults(func=self._cmd_status)
        check = subparsers.add_parser("check")
        check.set_defaults(func=self._cmd_check)
        previous = subparsers.add_parser("previous")
        previous.add_argument("--limit", type=int, default=5)
        previous.set_defaults(func=self._cmd_previous)
        return parser

    def _storage(self, args: argparse.Namespace) -> FileStorage:
        """Create storage from parsed CLI arguments.

        Args:
            args: Parsed namespace containing ``base_path``.
        """
        return FileStorage(Path(args.base_path))

    def _load_run(self, storage: FileStorage, run_id: str) -> Run:
        """Load a persisted run for CLI operations.

        Args:
            storage: Storage service containing the run.
            run_id: Identifier of the run to load.
        """
        data = storage.read_run(run_id)
        if not data:
            raise SystemExit(f"Run not found: {run_id}")
        try:
            research_data = data["research"]
            motivation_data = research_data["motivation"]
            execution_data = data["execution"]
            review_data = data["review"]
            motivation = Motivation(type=str(motivation_data["type"]), reference=motivation_data.get("reference"))
            execution = Execution(status=str(execution_data["status"]),
                                  started_at=self._parse_time(execution_data.get("started_at")),
                                  finished_at=self._parse_time(execution_data.get("finished_at")),
                                  error=execution_data.get("error"))
            review = Review(status=str(review_data.get("status", "needs_review")),
                            conclusion=review_data.get("conclusion"), next_step=review_data.get("next_step"))
            return Run(run_id=run_id,
                       research=ResearchMetadata(hypothesis=str(research_data["hypothesis"]), motivation=motivation),
                       storage=storage, path=storage.run_path(run_id), execution=execution, review=review)
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"Invalid run.yaml for {run_id}: {exc}") from exc

    def _cmd_new(self, args: argparse.Namespace) -> int:
        """Create and activate a new research run from CLI arguments.

        Args:
            args: Parsed ``new`` command arguments.
        """
        storage = self._storage(args)
        storage.initialize()
        if storage.get_active() is not None:
            raise SystemExit(f"Another run is already active: {storage.get_active()}")
        run_id = storage.next_run_id()
        run = Run(run_id=run_id,
                  research=ResearchMetadata(hypothesis=args.hypothesis,
                                             motivation=Motivation(args.motivation_type, args.reference)),
                  storage=storage, path=storage.run_path(run_id),
                  execution=Execution(status="running"), review=Review())
        storage.set_active(run_id)
        run.start()
        print(run_id)
        return 0

    def _cmd_finish(self, args: argparse.Namespace) -> int:
        """Attach human review to a completed run.

        Args:
            args: Parsed ``finish`` command arguments.
        """
        storage = self._storage(args)
        run_id = args.run_id or storage.get_active()
        if run_id is None:
            raise SystemExit("No run specified and no active run exists")
        run = self._load_run(storage, run_id)
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

    def _cmd_resume(self, args: argparse.Namespace) -> int:
        """Restore an active pointer for a running run.

        Args:
            args: Parsed ``resume`` command arguments.
        """
        storage = self._storage(args)
        run_id = args.run_id or storage.get_active()
        if run_id is None:
            raise SystemExit("No run specified and no active run exists")
        run = self._load_run(storage, run_id)
        if run.execution.status != "running":
            raise SystemExit(f"Only a running run can be resumed: {run_id} ({run.execution.status})")
        active = storage.get_active()
        if active is None:
            storage.set_active(run_id)
        elif active != run_id:
            raise SystemExit(f"Another run is already active: {active}")
        print(run_id)
        return 0

    def _cmd_check(self, args: argparse.Namespace) -> int:
        """Run read-only src consistency analysis and print its report.

        Args:
            args: Parsed ``check`` command arguments.
        """
        storage = self._storage(args)
        report = ResearchChecker(storage).check()
        self._print_report(report)
        return 0

    def _cmd_status(self, args: argparse.Namespace) -> int:
        """Print execution and review state of the active run.

        Args:
            args: Parsed ``status`` command arguments.
        """
        storage = self._storage(args)
        active = storage.get_active()
        if active is None:
            print("active: none")
            return 0
        run = self._load_run(storage, active)
        print(f"run_id: {run.run_id}")
        print(f"execution.status: {run.execution.status}")
        print(f"review.status: {run.review.status}")
        return 0

    def _cmd_previous(self, args: argparse.Namespace) -> int:
        """Print recent runs in chronological order.

        Args:
            args: Parsed ``previous`` command arguments, including ``limit``.
        """
        storage = self._storage(args)
        run_ids = storage.list_run_ids()[-args.limit:]
        if not run_ids:
            print("runs: none")
            return 0
        for run_id in run_ids:
            run = self._load_run(storage, run_id)
            motivation = run.research.motivation
            reference = f" -> {motivation.reference}" if motivation.reference else ""
            hypothesis = " ".join(run.research.hypothesis.split())
            print(f"{run.run_id} | execution={run.execution.status} | review={run.review.status} | motivation={motivation.type}{reference} | hypothesis={hypothesis}")
        return 0

    @staticmethod
    def _parse_time(value: object) -> datetime | None:
        """Parse a persisted ISO timestamp for CLI deserialization.

        Args:
            value: YAML timestamp value or ``None``.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    @staticmethod
    def _print_report(report: ConsistencyReport) -> None:
        """Print a consistency report in stable human-readable form.

        Args:
            report: Consistency report returned by ``ResearchChecker``.
        """
        print(f"completed runs: {len(report.completed_runs)}")
        print(f"runs with hypotheses: {len(report.runs_with_hypotheses)}")
        if report.issues:
            print("issues:")
            for issue in report.issues:
                print(f"  {issue.severity}: {issue.run_id}: {issue.code}: {issue.message}")
        else:
            print("issues: none")


CLI = ResearchCli()
"""Default CLI instance used by the module-level console entry point."""


main = CLI.main
"""Bound command-line entry point retained for backwards compatibility."""


if __name__ == "__main__":
    raise SystemExit(CLI.main())
