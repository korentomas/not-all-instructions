# experiments/tests/test_tool_executor.py
import pytest
from pathlib import Path
from harness.tool_executor import ToolExecutor
from harness.providers import ToolCall


@pytest.fixture
def executor(tmp_path):
    """Create a ToolExecutor with a small test repo."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    (repo / "main.py").write_text("def hello():\n    return 'world'\n")
    (repo / "utils.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "sub").mkdir()
    (repo / "sub" / "deep.py").write_text("import os\nprint(os.getcwd())\n")
    return ToolExecutor(repo_root=repo)


class TestReadFile:
    def test_read_existing_file(self, executor):
        result = executor.execute(ToolCall(name="read_file", arguments={"path": "main.py"}, id="1"))
        assert "def hello():" in result.content
        assert "main.py" in executor.files_read

    def test_read_nested_file(self, executor):
        result = executor.execute(ToolCall(name="read_file", arguments={"path": "sub/deep.py"}, id="2"))
        assert "import os" in result.content

    def test_read_nonexistent_file(self, executor):
        result = executor.execute(ToolCall(name="read_file", arguments={"path": "nope.py"}, id="3"))
        assert "not found" in result.content.lower() or "error" in result.content.lower()


class TestWriteFile:
    def test_write_logs_content(self, executor):
        result = executor.execute(ToolCall(name="write_file", arguments={"path": "main.py", "content": "new code"}, id="4"))
        assert "success" in result.content.lower() or "wrote" in result.content.lower()

    def test_write_tracks_path(self, executor):
        executor.execute(ToolCall(name="write_file", arguments={"path": "foo.py", "content": "x"}, id="5"))
        assert "foo.py" in executor.files_written


class TestSearchCode:
    def test_search_finds_pattern(self, executor):
        result = executor.execute(ToolCall(name="search_code", arguments={"pattern": "def hello"}, id="6"))
        assert "main.py" in result.content

    def test_search_no_results(self, executor):
        result = executor.execute(ToolCall(name="search_code", arguments={"pattern": "zzz_nonexistent"}, id="7"))
        assert "no matches" in result.content.lower() or result.content.strip() == ""


class TestRunCommand:
    def test_returns_scripted_output(self, executor):
        executor.set_scripted_output(turn=5, output="PASSED 12 tests")
        result = executor.execute(
            ToolCall(name="run_command", arguments={"command": "pytest"}, id="8"),
            current_turn=5,
        )
        assert "PASSED 12 tests" in result.content

    def test_unscripted_returns_placeholder(self, executor):
        result = executor.execute(
            ToolCall(name="run_command", arguments={"command": "pytest"}, id="9"),
            current_turn=99,
        )
        assert "command executed" in result.content.lower() or len(result.content) > 0

    def test_destructive_command_blocked(self, executor):
        result = executor.execute(
            ToolCall(name="run_command", arguments={"command": "rm -rf /"}, id="10"),
            current_turn=0,
        )
        assert "blocked" in result.content.lower() or "destructive" in result.content.lower()


class TestFilesReadTracking:
    def test_tracks_reads(self, executor):
        executor.execute(ToolCall(name="read_file", arguments={"path": "main.py"}, id="11"))
        executor.execute(ToolCall(name="read_file", arguments={"path": "utils.py"}, id="12"))
        assert executor.files_read == {"main.py", "utils.py"}
