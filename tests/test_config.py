"""Tests for :mod:`app.config`."""

from __future__ import annotations

import os
import pathlib

import pytest

from app import config


def test_constants_are_sane():
    assert config.APP_NAME == "SystemMonitor"
    assert config.APP_DISPLAY_NAME
    assert config.MIN_REFRESH_MS < config.DEFAULT_REFRESH_MS < config.MAX_REFRESH_MS
    assert config.MIN_HISTORY_SAMPLES < config.DEFAULT_HISTORY_SAMPLES
    assert config.DEFAULT_HISTORY_SAMPLES < config.MAX_HISTORY_SAMPLES


def test_app_data_directory_is_absolute_and_namespaced():
    directory = config.app_data_dir()
    assert directory.is_absolute()
    assert directory.name == config.APP_NAME


def test_logs_and_settings_live_under_the_data_directory():
    assert config.logs_dir().parent == config.app_data_dir()
    assert config.settings_path().parent == config.app_data_dir()
    assert config.log_file_path().parent == config.logs_dir()


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific layout")
def test_windows_layout_uses_appdata(monkeypatch):
    monkeypatch.setenv("APPDATA", r"C:\Users\tester\AppData\Roaming")
    assert str(config.app_data_dir()).endswith(
        os.path.join("tester", "AppData", "Roaming", config.APP_NAME)
    )


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific layout")
def test_windows_layout_falls_back_when_appdata_is_unset(monkeypatch, tmp_path):
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: tmp_path))
    assert config.APP_NAME in str(config.app_data_dir())


def test_is_windows_matches_the_platform():
    assert config.is_windows() == (os.name == "nt")


def test_is_frozen_is_false_when_running_from_source():
    assert config.is_frozen() is False


def test_ensure_directories_creates_the_tree():
    base = config.ensure_directories()
    assert base.is_dir()
    assert config.logs_dir().is_dir()


def test_project_root_contains_main():
    root = config.project_root()
    assert root.is_absolute()
    assert (root / "main.py").exists()
    assert (root / "app" / "config.py").exists()


def test_assets_directory_is_inside_the_project():
    assert config.assets_dir() == config.project_root() / "assets"
