"""Shared test fixtures for PyClaw."""

from __future__ import annotations

from pathlib import Path

import pytest

from pyclaw.config import PyClawConfig


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace directory."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


@pytest.fixture
def tmp_config(tmp_path: Path, tmp_workspace: Path) -> PyClawConfig:
    """Create a test config pointing to temporary directories."""
    return PyClawConfig(
        default_model="openai:gpt-4o",
        workspace=str(tmp_workspace),
        model_list=[],
    )


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    """Return a temporary config file path."""
    return tmp_path / "config.json"
