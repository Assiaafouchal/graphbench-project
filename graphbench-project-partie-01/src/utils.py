"""Utility helpers"""
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).parents[1]
