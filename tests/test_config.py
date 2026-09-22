import pytest

from app.config import (
    LabConfig,
    ProductionConfig,
    environment_config,
)


def set_required_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "a" * 32)
    monkeypatch.setenv("DB_USER", "shop_app")
    monkeypatch.setenv("DB_PASSWORD", "dummy-password")
    monkeypatch.setenv("DB_NAME", "shop")
    monkeypatch.setenv("DB_HOST", "127.0.0.1")


def test_lab_environment(monkeypatch):
    set_required_env(monkeypatch)
    monkeypatch.setenv("FLASK_ENV", "lab")
    monkeypatch.setenv("VULNERABLE_LAB", "1")

    config_class, values = environment_config()

    assert config_class is LabConfig
    assert config_class.SESSION_COOKIE_SECURE is True
    assert config_class.TRUST_PROXY_HEADERS is True
    assert values["VULNERABLE_LAB"] is True


def test_vulnerable_mode_rejected_in_production(monkeypatch):
    set_required_env(monkeypatch)
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("VULNERABLE_LAB", "1")

    with pytest.raises(ValueError):
        environment_config()


def test_production_fixed_mode(monkeypatch):
    set_required_env(monkeypatch)
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("VULNERABLE_LAB", "0")

    config_class, values = environment_config()

    assert config_class is ProductionConfig
    assert values["VULNERABLE_LAB"] is False