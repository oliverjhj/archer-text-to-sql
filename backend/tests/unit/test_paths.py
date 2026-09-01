"""
Unit tests for path resolution in archer.core.paths.

Verifies that BASE_DIR, STATIC_DIR, and TEMPLATES_DIR resolve to the expected
locations relative to the installed source tree.  No file I/O, no env vars,
no network access.
"""

import pytest
from pathlib import Path

from archer.core.paths import BASE_DIR, STATIC_DIR, TEMPLATES_DIR


@pytest.mark.unit
def test_base_dir_is_path_instance() -> None:
    """BASE_DIR is a pathlib.Path object."""
    assert isinstance(BASE_DIR, Path)


@pytest.mark.unit
def test_base_dir_is_absolute() -> None:
    """BASE_DIR resolves to an absolute path."""
    assert BASE_DIR.is_absolute()


@pytest.mark.unit
def test_base_dir_ends_with_backend() -> None:
    """BASE_DIR points two levels above paths.py, which is the backend/ directory."""
    assert BASE_DIR.name == "backend"


@pytest.mark.unit
def test_static_dir_is_base_dir_child() -> None:
    """STATIC_DIR is BASE_DIR / 'static'."""
    assert STATIC_DIR == BASE_DIR / "static"


@pytest.mark.unit
def test_templates_dir_is_base_dir_child() -> None:
    """TEMPLATES_DIR is BASE_DIR / 'templates'."""
    assert TEMPLATES_DIR == BASE_DIR / "templates"
