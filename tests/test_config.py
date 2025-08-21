"""Tests for configuration loading and path resolution."""

from pathlib import Path

import yaml

from multirec.config.config import Config, load_config


def test_load_config_uses_project_file(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("concurrency_limit: 7\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    config, path = load_config()

    assert path == cfg
    assert config.concurrency_limit == 7


def test_load_config_creates_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    config, path = load_config()

    expected = tmp_path / ".multirec" / "config.yaml"
    assert path == expected
    assert path.exists()

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data == Config().model_dump(mode="json")
    assert config == Config()

