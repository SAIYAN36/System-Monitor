"""Tests for :mod:`app.services.settings`."""

from __future__ import annotations

import json

import pytest

from app.config import (
    DEFAULT_HISTORY_SAMPLES,
    DEFAULT_REFRESH_MS,
    DEFAULT_TEMPERATURE_INTERVAL_S,
    MAX_HISTORY_SAMPLES,
    MAX_REFRESH_MS,
    MIN_HISTORY_SAMPLES,
    MIN_REFRESH_MS,
)
from app.services.settings import DASHBOARD_CARDS, DASHBOARD_GRAPHS, Settings, SettingsManager


@pytest.fixture
def manager(tmp_path):
    return SettingsManager(tmp_path / "settings.json")


class TestDefaults:
    def test_defaults_are_in_range(self):
        settings = Settings().normalize()
        assert MIN_REFRESH_MS <= settings.refresh_interval_ms <= MAX_REFRESH_MS
        assert MIN_HISTORY_SAMPLES <= settings.history_samples <= MAX_HISTORY_SAMPLES
        assert settings.theme == "dark"
        assert settings.temperature_enabled is True
        assert settings.confirm_terminate is True

    def test_every_dashboard_flag_defaults_to_on(self):
        settings = Settings().normalize()
        assert set(settings.dashboard_cards) == set(DASHBOARD_CARDS)
        assert set(settings.dashboard_graphs) == set(DASHBOARD_GRAPHS)
        assert all(settings.dashboard_cards.values())
        assert all(settings.dashboard_graphs.values())


class TestValidation:
    def test_refresh_interval_is_clamped(self):
        assert Settings(refresh_interval_ms=1).normalize().refresh_interval_ms == MIN_REFRESH_MS
        assert Settings(refresh_interval_ms=10**9).normalize().refresh_interval_ms == MAX_REFRESH_MS

    def test_history_samples_are_clamped(self):
        assert Settings(history_samples=0).normalize().history_samples == MIN_HISTORY_SAMPLES
        assert (
            Settings(history_samples=10**6).normalize().history_samples == MAX_HISTORY_SAMPLES
        )

    def test_temperature_interval_is_clamped(self):
        settings = Settings(temperature_interval_s=-4).normalize()
        assert settings.temperature_interval_s >= 5

    def test_unknown_theme_falls_back_to_dark(self):
        assert Settings(theme="neon").normalize().theme == "dark"

    def test_non_numeric_values_fall_back_to_defaults(self):
        settings = Settings(refresh_interval_ms="fast").normalize()
        assert settings.refresh_interval_ms == DEFAULT_REFRESH_MS
        assert Settings(temperature_interval_s="soon").normalize().temperature_interval_s == (
            DEFAULT_TEMPERATURE_INTERVAL_S
        )

    def test_boolean_fields_are_coerced(self):
        settings = Settings(start_minimized="yes", confirm_terminate=0).normalize()
        assert settings.start_minimized is True
        assert settings.confirm_terminate is False

    def test_missing_dashboard_keys_are_filled(self):
        settings = Settings(dashboard_cards={"cpu": False}).normalize()
        assert settings.dashboard_cards["cpu"] is False
        assert settings.dashboard_cards["memory"] is True

    def test_bad_geometry_type_is_dropped(self):
        assert Settings(window_geometry=1234).normalize().window_geometry is None


class TestPersistence:
    def test_defaults_when_file_is_missing(self, manager):
        settings = manager.load()
        assert settings.refresh_interval_ms == DEFAULT_REFRESH_MS
        assert not manager.path.exists()

    def test_round_trip(self, manager):
        manager.settings.refresh_interval_ms = 2500
        manager.settings.theme = "light"
        manager.settings.dashboard_cards["clock"] = False
        assert manager.save() is True

        reloaded = SettingsManager(manager.path).load()
        assert reloaded.refresh_interval_ms == 2500
        assert reloaded.theme == "light"
        assert reloaded.dashboard_cards["clock"] is False

    def test_saved_file_is_valid_json(self, manager):
        manager.save()
        payload = json.loads(manager.path.read_text(encoding="utf-8"))
        assert payload["theme"] == "dark"
        assert payload["refresh_interval_ms"] == DEFAULT_REFRESH_MS

    def test_corrupt_file_falls_back_to_defaults(self, manager):
        manager.path.write_text("{ this is not json", encoding="utf-8")
        assert manager.load().refresh_interval_ms == DEFAULT_REFRESH_MS

    def test_json_array_is_rejected(self, manager):
        manager.path.write_text("[1, 2, 3]", encoding="utf-8")
        assert manager.load().refresh_interval_ms == DEFAULT_REFRESH_MS

    def test_unknown_keys_are_ignored(self, manager):
        manager.path.write_text(
            json.dumps({"refresh_interval_ms": 2000, "mystery": True}), encoding="utf-8"
        )
        settings = manager.load()
        assert settings.refresh_interval_ms == 2000
        assert not hasattr(settings, "mystery")

    def test_out_of_range_file_values_are_repaired(self, manager):
        manager.path.write_text(
            json.dumps({"refresh_interval_ms": 5, "history_samples": 99_999}),
            encoding="utf-8",
        )
        settings = manager.load()
        assert settings.refresh_interval_ms == MIN_REFRESH_MS
        assert settings.history_samples == MAX_HISTORY_SAMPLES

    def test_save_leaves_no_temporary_files(self, manager):
        manager.save()
        leftovers = [
            item for item in manager.path.parent.iterdir() if item.name.startswith(".settings-")
        ]
        assert leftovers == []

    def test_reset_writes_defaults(self, manager):
        manager.settings.refresh_interval_ms = 5000
        manager.save()
        manager.reset()
        assert SettingsManager(manager.path).load().refresh_interval_ms == DEFAULT_REFRESH_MS
