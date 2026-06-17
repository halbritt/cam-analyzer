"""Tests for package-level metadata (issue #8)."""

import cam_analyzer


def test_version_is_non_empty_str():
    assert isinstance(cam_analyzer.__version__, str)
    assert cam_analyzer.__version__
