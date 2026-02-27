"""Tests for PyClaw CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from pyclaw.cli import app

runner = CliRunner()


def _patch_config_paths(tmp_path: Path, workspace: Path | None = None):
    """Return a context manager that patches all config paths to tmp_path."""
    workspace = workspace or tmp_path / "workspace"
    return (
        patch("pyclaw.config.DEFAULT_CONFIG_PATH", tmp_path / "config.json"),
        patch("pyclaw.config.DEFAULT_ENV_PATH", tmp_path / ".env"),
        patch("pyclaw.config.DEFAULT_CONFIG_DIR", tmp_path),
        patch("pyclaw.config.DEFAULT_WORKSPACE", workspace),
    )


def test_onboard_creates_config(tmp_path: Path):
    """Onboard should create config and workspace (two-step selection)."""
    p1, p2, p3, p4 = _patch_config_paths(tmp_path)

    # Two questionary.select calls: provider then model
    mock_provider = MagicMock()
    mock_provider.ask.return_value = "Ollama (local, no API key)"
    mock_model = MagicMock()
    mock_model.ask.return_value = "Llama 3.2"

    with p1, p2, p3, p4, patch("questionary.select", side_effect=[mock_provider, mock_model]):
        result = runner.invoke(app, ["onboard"])

    assert result.exit_code == 0


def test_status_no_config(tmp_path: Path):
    """Status should fail when no config exists."""
    fake = tmp_path / "nonexistent"
    p1, p2, p3, p4 = _patch_config_paths(fake)
    with p1, p2, p3, p4:
        result = runner.invoke(app, ["status"])

    assert result.exit_code == 1


def test_status_with_config(tmp_path: Path):
    """Status should display config summary."""
    from pyclaw.config import PyClawConfig, save_config

    config_path = tmp_path / "config.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    config = PyClawConfig(workspace=str(workspace))
    save_config(config, config_path)

    p1, p2, p3, p4 = _patch_config_paths(tmp_path, workspace)
    with p1, p2, p3, p4:
        result = runner.invoke(app, ["status"])

    assert result.exit_code == 0


def test_cron_list_empty(tmp_path: Path):
    """Cron list should work with no tasks configured."""
    from pyclaw.config import PyClawConfig, save_config

    config_path = tmp_path / "config.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    config = PyClawConfig(workspace=str(workspace))
    save_config(config, config_path)

    p1, p2, p3, p4 = _patch_config_paths(tmp_path, workspace)
    with p1, p2, p3, p4:
        result = runner.invoke(app, ["cron", "list"])

    assert result.exit_code == 0


def test_cron_list_with_tasks(tmp_path: Path):
    """Cron list should display tasks from HEARTBEAT.md."""
    from pyclaw.config import PyClawConfig, save_config

    config_path = tmp_path / "config.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    heartbeat = workspace / "HEARTBEAT.md"
    heartbeat.write_text("## Tasks\n- Check email\n- Summarize news\n")

    config = PyClawConfig(workspace=str(workspace))
    save_config(config, config_path)

    p1, p2, p3, p4 = _patch_config_paths(tmp_path, workspace)
    with p1, p2, p3, p4:
        result = runner.invoke(app, ["cron", "list"])

    assert result.exit_code == 0
