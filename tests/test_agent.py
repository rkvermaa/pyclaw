"""Tests for PyClaw agent and workspace."""

from __future__ import annotations

from pathlib import Path

from pyclaw.memory.loader import load_workspace_memory
from pyclaw.prompts import build_system_prompt
from pyclaw.sessions.manager import (
    get_channel_thread_id,
    get_checkpointer_path,
    get_default_thread_id,
    new_thread_id,
)
from pyclaw.tools import build_tools
from pyclaw.workspace import init_workspace


def test_init_workspace(tmp_workspace: Path):
    """Workspace init should create all template files."""
    created = init_workspace(tmp_workspace)

    assert len(created) == 5
    assert (tmp_workspace / "IDENTITY.md").exists()
    assert (tmp_workspace / "SOUL.md").exists()
    assert (tmp_workspace / "MEMORY.md").exists()
    assert (tmp_workspace / "USER.md").exists()
    assert (tmp_workspace / "HEARTBEAT.md").exists()
    assert (tmp_workspace / "sessions").is_dir()
    assert (tmp_workspace / "data").is_dir()


def test_init_workspace_idempotent(tmp_workspace: Path):
    """Second init should not overwrite existing files."""
    init_workspace(tmp_workspace)

    # Write custom content
    (tmp_workspace / "IDENTITY.md").write_text("Custom identity")

    created = init_workspace(tmp_workspace)
    assert len(created) == 0
    assert (tmp_workspace / "IDENTITY.md").read_text() == "Custom identity"


def test_load_workspace_memory(tmp_workspace: Path):
    """Memory loader should read all .md files."""
    init_workspace(tmp_workspace)
    memory = load_workspace_memory(tmp_workspace)

    assert "IDENTITY.md" in memory
    assert "SOUL.md" in memory
    assert "MEMORY.md" in memory
    assert "USER.md" in memory
    assert "HEARTBEAT.md" in memory
    assert "Agent Identity" in memory["IDENTITY.md"]


def test_load_workspace_memory_missing_files(tmp_workspace: Path):
    """Memory loader should handle missing files gracefully."""
    memory = load_workspace_memory(tmp_workspace)
    assert len(memory) == 0


def test_build_system_prompt():
    """System prompt should include all context sections."""
    prompt = build_system_prompt(
        agent_name="TestBot",
        identity="I am a test bot.",
        soul="Be testing.",
        user_profile="Tester",
        memory="Remember tests.",
        workspace_path="/tmp/test",
    )

    assert "TestBot" in prompt
    assert "I am a test bot." in prompt
    assert "Be testing." in prompt
    assert "Tester" in prompt
    assert "Remember tests." in prompt
    assert "/tmp/test" in prompt


def test_default_thread_id():
    """Default thread ID should be stable."""
    assert get_default_thread_id() == "pyclaw-interactive"


def test_new_thread_id():
    """New thread IDs should be unique."""
    id1 = new_thread_id()
    id2 = new_thread_id()
    assert id1 != id2
    assert id1.startswith("pyclaw-")


def test_channel_thread_id():
    """Channel thread IDs should include channel and user."""
    tid = get_channel_thread_id("telegram", "12345")
    assert tid == "pyclaw-telegram-12345"


def test_checkpointer_path(tmp_workspace: Path):
    """Checkpointer path should be in sessions directory."""
    path = get_checkpointer_path(tmp_workspace)
    assert path.name == "checkpoints.sqlite"
    assert "sessions" in str(path)


def test_build_tools_web_search_disabled(tmp_config):
    """When web search is disabled, no web search tool should be built."""
    tmp_config.tools.web_search.enabled = False
    tools = build_tools(tmp_config)
    tool_names = [t.name for t in tools]
    assert "web_search" not in tool_names


def test_build_tools_includes_cron(tmp_config):
    """Cron tools should always be included."""
    init_workspace(tmp_config.workspace_path)
    tools = build_tools(tmp_config)
    tool_names = [t.name for t in tools]
    assert "add_heartbeat_task" in tool_names
    assert "list_heartbeat_tasks" in tool_names
    assert "remove_heartbeat_task" in tool_names
