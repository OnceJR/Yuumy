"""Configuration management for the multistream recorder.

This module defines a Pydantic model representing the application
configuration and implements functions to load configuration from a YAML
file.  Defaults are provided for all fields so a missing configuration file
will not prevent the application from starting.  Users may override
configuration values via a YAML file on disk or by specifying a path when
starting the application.

Configuration values include:
 - ``download_dir``: Directory where recordings are saved.
 - ``db_path``: Path to the SQLite database file.
 - ``concurrency_limit``: Maximum number of concurrent recordings.
 - ``segment_duration_min``: Duration (minutes) of each recording segment.
 - ``retry_max_attempts``: Maximum number of reconnection attempts per stream.
 - ``backoff_base_seconds``: Base backoff time in seconds for retry logic.

Additional options may be added to this model as the application evolves.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, validator


class Config(BaseModel):
    """Pydantic model describing application configuration."""

    download_dir: Path = Field(default=Path.home() / "multirec_downloads",
                               description="Base directory for saved recordings")
    db_path: Path = Field(default=Path.home() / ".multirec.db",
                          description="Path to the SQLite database file")
    concurrency_limit: int = Field(default=4,
                                   description="Maximum number of concurrent recordings")
    segment_duration_min: int = Field(default=30,
                                      description="Length of each recording segment in minutes")
    retry_max_attempts: int = Field(default=5,
                                    description="Maximum number of reconnection attempts per stream")
    backoff_base_seconds: float = Field(default=5.0,
                                        description="Base seconds for exponential backoff")

    class Config:
        arbitrary_types_allowed = True

    @validator("concurrency_limit")
    def validate_concurrency(cls, v: int) -> int:
        if v < 1:
            raise ValueError("concurrency_limit must be at least 1")
        return v

    @validator("segment_duration_min")
    def validate_segment_duration(cls, v: int) -> int:
        if v < 1:
            raise ValueError("segment_duration_min must be at least 1 minute")
        return v


def load_config(path: Optional[str] = None) -> Config:
    """Loads configuration from a YAML file or returns defaults.

    Args:
        path: Optional path to a YAML configuration file.  If omitted, the
            default config path ``~/.multirec/config.yaml`` is used if it exists.

    Returns:
        Config: Loaded configuration object.
    """
    default_path = Path.home() / ".multirec" / "config.yaml"
    config_file = Path(path) if path else default_path
    data: dict = {}
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                print(f"Warning: failed to parse config file {config_file}: {e}")
    return Config(**data)