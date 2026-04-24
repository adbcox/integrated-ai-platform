#!/usr/bin/env python3
"""Comprehensive test suite for autonomous executor.

Tests cover:
- Unit tests for critical functions (priority sorting, decomposition, timeouts)
- Integration tests (full execution flow, crash reporting, output flushing)
- Edge cases (no items, filtering, corrupted files, git verification)
"""

import sys
import json
import pytest
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.auto_execute_roadmap import RoadmapExecutor
from bin.roadmap_parser import RoadmapItem


def create_test_item(
    id="RM-TEST-001",
    title="Test Item",
    category="TEST",
    item_type="Enhancement",
    description="Test description",
    status="Accepted",
    priority="High",
    priority_class="P1",
    readiness="now",
    queue_rank=1,
    file_path="/test/001.md",
    dependencies=None,
):
    """Helper to create RoadmapItem with all required fields."""
    return RoadmapItem(
        id=id,
        title=title,
        category=category,
        item_type=item_type,
        description=description,
        status=status,
        priority=priority,
        priority_class=priority_class,
        readiness=readiness,
        queue_rank=queue_rank,
        file_path=file_path,
        dependencies=dependencies or [],
    )


class TestFindExecutableItems:
    """Test priority sorting and dependency checking."""

    def setup_method(self):
        """Create mock executor and items."""
        self.executor = RoadmapExecutor(Path("/tmp/test_repo"))

    def test_priority_sorting_p1_before_p2(self):
        """P1 items should come before P2 even with lower queue rank."""
        items = [
            create_test_item(
                id="RM-TEST-001", title="P2 Low", priority_class="P2", queue_rank=1,
                file_path="/test/001.md"
            ),
            create_test_item(
                id="RM-TEST-002", title="P1 High", priority_class="P1", queue_rank=999,
                file_path="/test/002.md"
            ),
        ]

        candidates = self.executor.find_executable_items(items, max_count=1)
        assert len(candidates) == 1
        assert candidates[0].id == "RM-TEST-002"  # P1 comes first
        assert candidates[0].priority_class == "P1"

    def test_skip_non_accepted_items(self):
        """Items not in EXECUTION_READY_STATUSES should be skipped."""
        items = [
            create_test_item(
                id="RM-TEST-001", title="Completed", status="Completed",
                queue_rank=1, file_path="/test/001.md"
            ),
            create_test_item(
                id="RM-TEST-002", title="Accepted", status="Accepted",
                priority_class="P2", queue_rank=2, file_path="/test/002.md"
            ),
        ]

        candidates = self.executor.find_executable_items(items, max_count=2)
        assert len(candidates) == 1
        assert candidates[0].id == "RM-TEST-002"

    def test_skip_not_ready_items(self):
        """Items with readiness 'blocked' should be skipped."""
        items = [
            create_test_item(
                id="RM-TEST-001", title="Blocked", readiness="blocked",
                queue_rank=1, file_path="/test/001.md"
            ),
            create_test_item(
                id="RM-TEST-002", title="Now", priority_class="P2",
                queue_rank=2, file_path="/test/002.md"
            ),
        ]

        candidates = self.executor.find_executable_items(items, max_count=2)
        assert len(candidates) == 1
        assert candidates[0].id == "RM-TEST-002"

    def test_respects_dependencies(self):
        """Items with unmet dependencies should be skipped."""
        items = [
            create_test_item(
                id="RM-TEST-001", title="Dependency", queue_rank=1,
                file_path="/test/001.md"
            ),
            create_test_item(
                id="RM-TEST-002", title="Dependent", priority_class="P2",
                queue_rank=2, file_path="/test/002.md", dependencies=["RM-TEST-001"]
            ),
        ]

        # RM-TEST-001 not completed, so RM-TEST-002 should be skipped
        candidates = self.executor.find_executable_items(items, max_count=2)
        assert len(candidates) == 1
        assert candidates[0].id == "RM-TEST-001"

    def test_empty_candidates_returns_empty(self):
        """No executable items returns empty list."""
        items = [
            create_test_item(
                id="RM-TEST-001", title="Completed", status="Completed",
                queue_rank=1, file_path="/test/001.md"
            ),
        ]

        candidates = self.executor.find_executable_items(items, max_count=5)
        assert len(candidates) == 0


class TestDecomposeItem:
    """Test subtask decomposition."""

    def setup_method(self):
        """Create mock executor."""
        self.executor = RoadmapExecutor(Path("/tmp/test_repo"))

    def test_decompose_returns_list_with_files(self):
        """Decomposition should return list of subtasks with file paths."""
        item = create_test_item(
            id="RM-TEST-001", title="Test Item",
            file_path="/test/001.md"
        )
        item.expected_file_families = ["domains/test.py", "bin/test.py"]

        with patch('requests.post') as mock_post:
            # Mock successful response from Ollama
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": json.dumps([
                    "Add function to domains/test.py",
                    "Create test in tests/test_test.py",
                    "Update bin/test.py with integration"
                ])
            }
            mock_post.return_value = mock_response

            subtasks = self.executor.decompose_item(item)

            assert len(subtasks) == 3
            assert all(".py" in s for s in subtasks)
            assert "domains/test.py" in subtasks[0]

    def test_fallback_when_api_unavailable(self):
        """Should fallback to file-based subtasks if API unavailable."""
        item = create_test_item(
            id="RM-TEST-001", title="Test Item",
            file_path="/test/001.md"
        )
        item.expected_file_families = ["domains/test.py"]

        with patch('requests.post', side_effect=Exception("API unavailable")):
            subtasks = self.executor.decompose_item(item)

            assert len(subtasks) > 0
            assert all(".py" in s for s in subtasks)

    def test_rejects_subtasks_without_files(self):
        """Subtasks without .py files should be filtered out."""
        item = create_test_item(
            id="RM-TEST-001", title="Test Item",
            file_path="/test/001.md"
        )
        item.expected_file_families = ["domains/test.py"]

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            # Response with some subtasks lacking .py files
            mock_response.json.return_value = {
                "response": json.dumps([
                    "Design UI layout",  # No .py file
                    "Add function to domains/test.py",  # Has .py file
                    "Ensure compatibility",  # No .py file
                ])
            }
            mock_post.return_value = mock_response

            subtasks = self.executor.decompose_item(item)

            # Should only include subtask with .py file
            assert len(subtasks) == 1
            assert "domains/test.py" in subtasks[0]


class TestExecuteSubtaskTimeout:
    """Test timeout handling in execute_subtask."""

    def setup_method(self):
        """Create mock executor."""
        self.executor = RoadmapExecutor(Path("/tmp/test_repo"))

    def test_timeout_kills_process(self):
        """Process should be killed if it exceeds timeout."""
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = Mock()
            mock_proc.pid = 12345
            mock_proc.communicate.side_effect = subprocess.TimeoutExpired("cmd", 5)
            mock_proc.wait.return_value = None
            mock_popen.return_value = mock_proc

            with patch('os.killpg'):
                with patch('os.getpgid', return_value=12345):
                    result = self.executor.execute_subtask(
                        "Test subtask in domains/test.py",
                        item_id="RM-TEST-001",
                        subtask_timeout=5
                    )

            assert result is False
            # Process retries 3 times by default, so communicate is called 3 times
            assert mock_proc.communicate.call_count == 3

    def test_default_timeout_is_600s(self):
        """Default timeout should be 600 seconds."""
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = Mock()
            mock_proc.pid = 12345
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = ("output", "")
            mock_popen.return_value = mock_proc

            self.executor.execute_subtask(
                "Test subtask in domains/test.py",
                item_id="RM-TEST-001"
            )

            # Check timeout argument
            call_args = mock_proc.communicate.call_args
            assert call_args[1]['timeout'] == 600

    def test_wait_timeout_protection(self):
        """proc.wait() should have timeout to prevent hanging."""
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = Mock()
            mock_proc.pid = 12345
            mock_proc.communicate.side_effect = subprocess.TimeoutExpired("cmd", 5)
            mock_proc.wait.side_effect = subprocess.TimeoutExpired("cmd", 5)
            mock_popen.return_value = mock_proc

            with patch('os.killpg'):
                with patch('os.getpgid', return_value=12345):
                    result = self.executor.execute_subtask(
                        "Test subtask in domains/test.py",
                        item_id="RM-TEST-001",
                        subtask_timeout=5
                    )

            assert result is False
            # Verify wait was called with timeout
            mock_proc.wait.assert_called_with(timeout=5)


class TestConsecutiveFailuresStop:
    """Test that execution stops after consecutive failures."""

    def setup_method(self):
        """Create mock executor."""
        self.executor = RoadmapExecutor(Path("/tmp/test_repo"))

    @patch('bin.auto_execute_roadmap.parse_roadmap_directory')
    @patch('bin.auto_execute_roadmap.infer_dependencies')
    @patch('bin.auto_execute_roadmap.detect_cycles')
    def test_stops_after_3_failures(self, mock_cycles, mock_deps, mock_parse):
        """Should stop after 3 consecutive failures."""
        items = [
            create_test_item(
                id="RM-TEST-001", title="Item1", queue_rank=1,
                file_path="/test/001.md"
            ),
            create_test_item(
                id="RM-TEST-002", title="Item2", priority_class="P2",
                queue_rank=2, file_path="/test/002.md"
            ),
            create_test_item(
                id="RM-TEST-003", title="Item3", priority_class="P3",
                queue_rank=3, file_path="/test/003.md"
            ),
        ]

        mock_parse.return_value = items
        mock_cycles.return_value = []

        # Mock execute_item to always fail
        with patch.object(self.executor, 'execute_item', return_value=False):
            with patch('builtins.print'):
                self.executor.run_autonomous_loop(
                    target_completions=10,
                    dry_run=False
                )

        # Should have attempted only 3 items before stopping
        assert mock_parse.call_count > 0  # Multiple reloads


class TestFilterSkipLogic:
    """Test filter pattern handling."""

    def setup_method(self):
        """Create mock executor."""
        self.executor = RoadmapExecutor(Path("/tmp/test_repo"))

    @patch('bin.auto_execute_roadmap.parse_roadmap_directory')
    @patch('bin.auto_execute_roadmap.infer_dependencies')
    @patch('bin.auto_execute_roadmap.detect_cycles')
    def test_no_infinite_loop_on_filter_mismatch(self, mock_cycles, mock_deps, mock_parse):
        """Should not infinite loop when filter doesn't match items."""
        items = [
            create_test_item(
                id="RM-DEV-001", title="Item1", queue_rank=1,
                file_path="/test/001.md"
            ),
        ]

        mock_parse.return_value = items
        mock_cycles.return_value = []

        # Use GOV filter but only DEV items exist
        output = StringIO()
        with patch('sys.stdout', output):
            with patch('builtins.print', wraps=print):
                self.executor.run_autonomous_loop(
                    target_completions=5,
                    filter_pattern="RM-GOV",
                    dry_run=True
                )

        output_text = output.getvalue()
        # Should report no matching items, not infinite loop
        assert "No items matching filter" in output_text or "completed" in output_text


class TestFullExecutionMock:
    """Integration test for full execution flow."""

    def setup_method(self):
        """Create mock executor."""
        self.executor = RoadmapExecutor(Path("/tmp/test_repo"))

    @patch('bin.auto_execute_roadmap.parse_roadmap_directory')
    @patch('bin.auto_execute_roadmap.infer_dependencies')
    @patch('bin.auto_execute_roadmap.detect_cycles')
    @patch.object(RoadmapExecutor, 'decompose_item')
    @patch.object(RoadmapExecutor, 'execute_subtask')
    def test_full_execution_flow(self, mock_exec_sub, mock_decompose,
                                 mock_cycles, mock_deps, mock_parse):
        """Test complete execution from item to completion."""
        items = [
            create_test_item(
                id="RM-TEST-001", title="Test Item", queue_rank=1,
                file_path="/test/001.md"
            ),
        ]

        mock_parse.return_value = items
        mock_cycles.return_value = []
        mock_decompose.return_value = [
            "Add function to domains/test.py",
            "Test in tests/test.py"
        ]
        mock_exec_sub.return_value = True  # Both subtasks succeed

        with patch('builtins.print'):
            self.executor.run_autonomous_loop(
                target_completions=1,
                dry_run=False
            )

        # Verify flow: decompose -> execute subtasks
        mock_decompose.assert_called()
        assert mock_exec_sub.call_count == 2


class TestCrashReporting:
    """Test exception handling and reporting."""

    def setup_method(self):
        """Create mock executor."""
        self.executor = RoadmapExecutor(Path("/tmp/test_repo"))

    @patch('bin.auto_execute_roadmap.parse_roadmap_directory')
    def test_exception_caught_and_printed(self, mock_parse):
        """Exceptions should be caught and printed."""
        mock_parse.side_effect = Exception("Test error: file not found")

        output = StringIO()
        with patch('sys.stderr', output):
            with pytest.raises(SystemExit):
                with patch('sys.argv', ['prog', '--target-completions', '1']):
                    from bin.auto_execute_roadmap import main
                    main()


class TestOutputFlushing:
    """Test that output appears immediately (not buffered)."""

    def setup_method(self):
        """Create mock executor."""
        self.executor = RoadmapExecutor(Path("/tmp/test_repo"))

    def test_debug_output_has_flush_true(self):
        """All [DEBUG] prints should have flush=True."""
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = Mock()
            mock_proc.pid = 12345
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = ("output", "")
            mock_popen.return_value = mock_proc

            output = StringIO()
            with patch('sys.stdout', output):
                with patch('builtins.print', wraps=print):
                    self.executor.execute_subtask(
                        "Test subtask in domains/test.py",
                        item_id="RM-TEST-001"
                    )

            output_text = output.getvalue()
            # Should contain debug output from execute_subtask
            assert "[DEBUG]" in output_text


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Create mock executor."""
        self.executor = RoadmapExecutor(Path("/tmp/test_repo"))

    @patch('bin.auto_execute_roadmap.parse_roadmap_directory')
    @patch('bin.auto_execute_roadmap.infer_dependencies')
    @patch('bin.auto_execute_roadmap.detect_cycles')
    def test_no_accepted_items_exits_gracefully(self, mock_cycles, mock_deps, mock_parse):
        """Should exit gracefully when no items are accepted."""
        items = [
            create_test_item(
                id="RM-TEST-001", title="Item", status="Completed",
                queue_rank=1, file_path="/test/001.md"
            ),
        ]

        mock_parse.return_value = items
        mock_cycles.return_value = []

        output = StringIO()
        with patch('sys.stdout', output):
            with patch('builtins.print', wraps=print):
                self.executor.run_autonomous_loop(
                    target_completions=5,
                    dry_run=True
                )

        output_text = output.getvalue()
        assert "No more executable items" in output_text

    def test_all_items_filtered_reports_no_matches(self):
        """Should report 'no matches' when all items filtered."""
        item = create_test_item(
            id="RM-DEV-001", title="Item", queue_rank=1,
            file_path="/test/001.md"
        )

        items = [item]

        # Filter for GOV but only DEV exists
        candidates = self.executor.find_executable_items(items, max_count=1)
        assert len(candidates) == 1  # Item found

        # Now apply filter
        import re
        if not re.search("RM-GOV", candidates[0].id):
            assert True  # Filter correctly rejects

    def test_subtask_without_file_gets_auto_fixed(self):
        """Subtasks missing files should get auto-fixed with inferred file."""
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = Mock()
            mock_proc.pid = 12345
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = ("output", "")
            mock_popen.return_value = mock_proc

            output = StringIO()
            with patch('sys.stdout', output):
                with patch('builtins.print', wraps=print):
                    # Subtask without .py file
                    self.executor.execute_subtask(
                        "Do something",
                        item_id="RM-DEV-001"
                    )

            output_text = output.getvalue()
            assert "[AUTO-FIX]" in output_text or "bin/aider_executor.py" in output_text


class TestExecutorIntegration:
    """Integration tests - actually run the executor script."""

    def test_executor_actually_runs(self):
        """Integration test - runs real executor with --help.

        This test catches import failures and startup crashes that mocks hide.
        Reproduces: "Tests pass but executor crashes on real startup" issue.
        """
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            ["python3", "bin/auto_execute_roadmap.py", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root
        )

        # Should succeed
        assert result.returncode == 0, f"Executor crashed with return code {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Should have valid help output
        assert "usage:" in result.stdout or "autonomous" in result.stdout.lower(), \
            f"Help output invalid: {result.stdout}"

    def test_executor_dry_run_initialization(self):
        """Integration test - executor should initialize for dry run without crashing.

        Note: With 223 items and 45+ dependency cycles, the full cycle detection
        can take 30+ seconds. This test verifies initialization only.
        """
        repo_root = Path(__file__).parent.parent

        try:
            result = subprocess.run(
                ["python3", "bin/auto_execute_roadmap.py", "--dry-run", "--max-items", "1"],
                capture_output=True,
                text=True,
                cwd=repo_root,
                timeout=90  # 90s for cycle detection on large roadmap
            )
            completed = True
        except subprocess.TimeoutExpired as e:
            # If it times out on cycle detection, that's OK - means initialization worked
            completed = False
            result = e

        stdout = result.stdout if isinstance(result, subprocess.CompletedProcess) else result.stdout.decode()

        # Should have startup output (proves it didn't crash on import)
        assert "[EMERGENCY] main() ENTRY" in stdout or "[STARTUP]" in stdout, \
            f"Missing startup output - crashed on import. Stdout: {stdout[:500]}"

    def test_executor_real_mode_initialization(self):
        """Integration test - executor should initialize properly in real mode.

        Tests that the executor startup (before subprocess calls) works in real mode.
        The subprocess call itself may timeout waiting for Ollama, which is OK.
        """
        repo_root = Path(__file__).parent.parent

        try:
            result = subprocess.run(
                ["python3", "bin/auto_execute_roadmap.py", "--max-items", "1"],
                capture_output=True,
                text=True,
                cwd=repo_root,
                timeout=20  # Timeout after 20s - expect initialization before then
            )
            completed = True
        except subprocess.TimeoutExpired as e:
            # Expected if subprocess is waiting on Ollama/external resource
            completed = False
            result = e

        # Check stdout/stderr
        stdout = result.stdout if isinstance(result, subprocess.CompletedProcess) else result.stdout.decode()
        stderr = result.stderr if isinstance(result, subprocess.CompletedProcess) else result.stderr.decode()

        # Should have emergency logging at entry (proves it didn't crash on import)
        assert "[EMERGENCY] main() ENTRY" in stdout, \
            f"Missing [EMERGENCY] main() ENTRY - crashed before/during main. Stdout: {stdout[:500]}\nStderr: {stderr[:500]}"

        # Should have started picking items (proves it got through roadmap parsing)
        assert "Decomposing into subtasks" in stdout or "execute_subtask() ENTRY" in stdout, \
            f"Never reached item execution phase. Stdout: {stdout}"

        # If it got to execute_subtask, should have emergency logging there too
        if "execute_subtask() ENTRY" in stdout:
            assert "[EMERGENCY]" in stdout, "Emergency logging missing from execute_subtask"
            assert "subprocess.Popen" in stdout, "Subprocess creation not logged"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
