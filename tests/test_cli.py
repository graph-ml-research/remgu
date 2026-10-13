# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Tests for the ResearchCli command interface."""
from __future__ import annotations

import contextlib
import io
import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

from remgu.research_cli import main
from remgu import Experiment
from remgu.models import Motivation


class TestResearchCli(unittest.TestCase):
    """Verify command-line lifecycle operations and output."""

    def setUp(self) -> None:
        """Create an isolated CLI storage directory."""
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self._temporary_directory.name) / ".research"

    def tearDown(self) -> None:
        """Remove the isolated CLI storage directory."""
        self._temporary_directory.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str]:
        """Run the CLI and capture standard output.

        Args:
            args: Command-line arguments following the executable name.
        """
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(("--base-path", str(self.base), *args))
        return code, output.getvalue()

    def read_run(self, run_id: str = "run-001") -> dict[str, Any]:
        """Load persisted run metadata.

        Args:
            run_id: Identifier of the run to load.
        """
        return yaml.safe_load((self.base / "runs" / run_id / "run.yaml").read_text(encoding="utf-8"))

    def test_new_creates_running_execution_and_pending_review(self) -> None:
        """Create a running run with an unreviewed state."""
        code, _ = self.run_cli("new", "--hypothesis", "H1", "--motivation-type", "new")
        self.assertEqual(code, 0)
        data = self.read_run()
        self.assertEqual(data["execution"]["status"], "running")
        self.assertEqual(data["review"]["status"], "needs_review")
        self.assertEqual((self.base / "active").read_text().strip(), "run-001")

    def test_new_forbids_second_active_run(self) -> None:
        """Reject creation while another run remains active."""
        self.run_cli("new", "--hypothesis", "H1")
        with self.assertRaisesRegex(SystemExit, "already active"):
            self.run_cli("new", "--hypothesis", "H2")

    def test_resume_restores_missing_active_pointer_without_changing_state(self) -> None:
        """Restore a missing active pointer for a still-running run."""
        self.run_cli("new", "--hypothesis", "H1")
        (self.base / "active").unlink()
        code, _ = self.run_cli("resume", "run-001")
        self.assertEqual(code, 0)
        data = self.read_run()
        self.assertEqual(data["execution"]["status"], "running")
        self.assertEqual(data["review"]["status"], "needs_review")
        self.assertEqual((self.base / "active").read_text().strip(), "run-001")

    def test_resume_rejects_terminal_run(self) -> None:
        """Reject resuming a terminal execution."""
        self.run_cli("new", "--hypothesis", "H1")
        (self.base / "active").unlink()
        data = self.read_run()
        data["execution"]["status"] = "completed"
        data["execution"]["finished_at"] = "2026-09-25T10:00:00Z"
        (self.base / "runs" / "run-001" / "run.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "Only a running run"):
            self.run_cli("resume", "run-001")

    def test_finish_moves_review_to_reviewed(self) -> None:
        """Attach conclusion and next step to a completed run."""
        self.run_cli("new", "--hypothesis", "H1")
        data = self.read_run()
        data["execution"]["status"] = "completed"
        data["execution"]["finished_at"] = "2026-09-25T10:00:00Z"
        (self.base / "runs" / "run-001" / "run.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        (self.base / "active").unlink()
        code, _ = self.run_cli("finish", "run-001", "--conclusion", "H1 supported", "--next-step", "Run H2")
        self.assertEqual(code, 0)
        self.assertEqual(self.read_run()["review"], {"status": "reviewed", "conclusion": "H1 supported", "next_step": "Run H2"})

    def test_finish_requires_completed_execution(self) -> None:
        """Reject review before execution is complete."""
        self.run_cli("new", "--hypothesis", "H1")
        with self.assertRaisesRegex(SystemExit, "completed execution"):
            self.run_cli("finish", "run-001", "--conclusion", "x", "--next-step", "y")

    def test_finish_requires_both_review_fields(self) -> None:
        """Require both conclusion and next step for review."""
        self.run_cli("new", "--hypothesis", "H1")
        data = self.read_run()
        data["execution"]["status"] = "completed"
        data["execution"]["finished_at"] = "2026-09-25T10:00:00Z"
        (self.base / "runs" / "run-001" / "run.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        (self.base / "active").unlink()
        with self.assertRaisesRegex(SystemExit, "--conclusion is required"):
            self.run_cli("finish", "run-001", "--next-step", "y")
        with self.assertRaisesRegex(SystemExit, "--next-step is required"):
            self.run_cli("finish", "run-001", "--conclusion", "x")

    def test_status_reports_both_lifecycles(self) -> None:
        """Print execution and review states for the active run."""
        self.run_cli("new", "--hypothesis", "H1")
        code, output = self.run_cli("status")
        self.assertEqual(code, 0)
        self.assertIn("execution.status: running", output)
        self.assertIn("review.status: needs_review", output)

    def test_previous_lists_recent_runs_oldest_first(self) -> None:
        """List recent runs in ascending run-id order."""
        self.run_cli("new", "--hypothesis", "First hypothesis", "--motivation-type", "new")
        (self.base / "active").unlink()
        self.run_cli("new", "--hypothesis", "Second hypothesis", "--motivation-type", "previous_run", "--reference", "run-001")
        (self.base / "active").unlink()
        _, output = self.run_cli("previous")
        lines = [line for line in output.splitlines() if line]
        self.assertTrue(lines[0].startswith("run-001 | execution=running | review=needs_review"))
        self.assertTrue(lines[1].startswith("run-002 | execution=running | review=needs_review"))
        self.assertIn("motivation=previous_run -> run-001", lines[1])
        self.assertIn("hypothesis=Second hypothesis", lines[1])

    def test_previous_limit_returns_only_requested_number(self) -> None:
        """Limit the number of runs displayed by the previous command."""
        for index in range(3):
            self.run_cli("new", "--hypothesis", f"H{index + 1}")
            (self.base / "active").unlink()
        _, output = self.run_cli("previous", "--limit", "2")
        lines = [line for line in output.splitlines() if line]
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("run-002 |"))
        self.assertTrue(lines[1].startswith("run-003 |"))

    def test_previous_when_no_runs(self) -> None:
        """Report an empty research store clearly."""
        _, output = self.run_cli("previous")
        self.assertEqual(output.strip(), "runs: none")

class TestResearchPublicationCli(unittest.TestCase):
    """Verify snapshot and archive CLI publication commands."""

    def setUp(self) -> None:
        """Create an isolated CLI research store."""
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self._temporary_directory.name) / ".research"

    def tearDown(self) -> None:
        """Remove the isolated research store."""
        self._temporary_directory.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str]:
        """Run the CLI and capture standard output.

        Args:
            args: Command-line arguments following the executable name.
        """
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(("--base-path", str(self.base), *args))
        return code, output.getvalue()

    def test_update_is_read_only_on_empty_project(self) -> None:
        """Build an empty snapshot without creating research files."""
        code, output = self.run_cli("update")
        self.assertEqual(code, 0)
        self.assertIn("Research updated.", output)
        self.assertIn("Runs: 0", output)
        self.assertFalse(self.base.exists())

    def test_archive_cli_creates_requested_output(self) -> None:
        """Create a ZIP archive at the requested destination."""
        code, output = self.run_cli("archive", "--output", str(Path(self._temporary_directory.name) / "out.zip"))
        self.assertEqual(code, 0)
        self.assertTrue(Path(output.strip()).exists())

    def test_site_cli_can_enrich_examples_with_importable_provider(self) -> None:
        """Load an application provider only when description enrichment is requested."""
        experiment = Experiment("graph-mamba", self.base)
        with experiment.run("H1", Motivation(type="new")) as run:
            run.collect({"example_id": "node-42", "score": 0.91})

        provider_dir = Path(self._temporary_directory.name) / "provider"
        provider_dir.mkdir()
        (provider_dir / "fixture_provider.py").write_text(
            """class Provider:
    def get(self, example_id): return {"id": example_id}
    def describe(self, example_id): return f"Fixture description for {example_id}"
""",
            encoding="utf-8",
        )
        sys.path.insert(0, str(provider_dir))
        importlib.invalidate_caches()
        try:
            output = Path(self._temporary_directory.name) / "site"
            code, _ = self.run_cli(
                "export", "site", "--output", str(output),
                "--describe-examples", "--example-provider", "fixture_provider:Provider",
            )
        finally:
            sys.path.remove(str(provider_dir))
            sys.modules.pop("fixture_provider", None)
            importlib.invalidate_caches()
        self.assertEqual(code, 0)
        page = (output / "examples" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Fixture description for node-42", page)

    def test_export_markdown_cli_creates_requested_output(self) -> None:
        """Export the empty snapshot as a standalone Markdown document."""
        destination = Path(self._temporary_directory.name) / "research.md"
        code, output = self.run_cli("export", "markdown", "--output", str(destination))
        self.assertEqual(code, 0)
        self.assertEqual(Path(output.strip()), destination)
        content = destination.read_text(encoding="utf-8")
        self.assertIn("# Research report", content)
        self.assertIn("Total runs: 0", content)
        self.assertFalse(self.base.exists())

    def test_export_markdown_cli_refuses_to_overwrite(self) -> None:
        """Preserve an existing report instead of overwriting it implicitly."""
        destination = Path(self._temporary_directory.name) / "research.md"
        destination.write_text("keep me", encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "already exists"):
            self.run_cli("export", "markdown", "--output", str(destination))
        self.assertEqual(destination.read_text(encoding="utf-8"), "keep me")

    def test_export_site_cli_creates_static_site(self) -> None:
        """Export an empty snapshot to the requested static site directory."""
        destination = Path(self._temporary_directory.name) / "site"
        code, output = self.run_cli("export", "site", "--output", str(destination))
        self.assertEqual(code, 0)
        self.assertEqual(Path(output.strip()), destination)
        self.assertTrue((destination / "index.html").is_file())
        self.assertTrue((destination / "style.css").is_file())
        self.assertTrue((destination / "examples" / "index.html").is_file())
        self.assertFalse(self.base.exists())

    def test_export_site_refuses_output_inside_research_store(self) -> None:
        """Keep generated publication artifacts outside the source-of-truth tree."""
        destination = self.base / "site"
        with self.assertRaisesRegex(SystemExit, "outside the research data directory"):
            self.run_cli("export", "site", "--output", str(destination))
        self.assertFalse(self.base.exists())

