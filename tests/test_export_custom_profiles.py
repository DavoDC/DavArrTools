"""Tests for export_custom_profiles.py"""

import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from export_custom_profiles import transform_profile, save_profile


# Minimal arr API profile response
SAMPLE_PROFILE = {
    "id": 5,
    "name": "My Custom Profile",
    "upgradeAllowed": True,
    "cutoff": 3,
    "minFormatScore": 0,
    "cutoffFormatScore": 10000,
    "minUpgradeFormatScore": 1,
    "language": {"id": -2, "name": "Original"},
    "items": [
        {
            "quality": {"id": 3, "name": "Remux-1080p", "source": "bluray", "resolution": 1080},
            "items": [],
            "allowed": True
        },
        {
            "id": 1001,
            "name": "WEB 1080p",
            "items": [
                {"quality": {"id": 7, "name": "WEBDL-1080p", "source": "web", "resolution": 1080}, "items": [], "allowed": True},
                {"quality": {"id": 8, "name": "WEBRip-1080p", "source": "webrip", "resolution": 1080}, "items": [], "allowed": True},
            ],
            "allowed": True
        },
        {
            "quality": {"id": 99, "name": "Unknown", "source": "unknown", "resolution": 0},
            "items": [],
            "allowed": False
        }
    ],
    "formatItems": [
        {"format": 1, "name": "HDR", "score": 50},
        {"format": 2, "name": "DV", "score": 100},
        {"format": 3, "name": "LQ", "score": -100},
    ]
}


def test_transform_strips_id():
    result = transform_profile(SAMPLE_PROFILE)
    assert "id" not in result


def test_transform_language_string():
    result = transform_profile(SAMPLE_PROFILE)
    assert result["language"] == "Original"


def test_transform_cutoff_name():
    """cutoff int ID should be resolved to quality name."""
    result = transform_profile(SAMPLE_PROFILE)
    assert result["cutoff"] == "Remux-1080p"


def test_transform_format_items_dict():
    """formatItems list should become {name: score} dict."""
    result = transform_profile(SAMPLE_PROFILE)
    assert result["formatItems"] == {"HDR": 50, "DV": 100, "LQ": -100}


def test_transform_items_single_quality():
    """Single quality items should have name and allowed only."""
    result = transform_profile(SAMPLE_PROFILE)
    remux = next(i for i in result["items"] if i["name"] == "Remux-1080p")
    assert remux == {"name": "Remux-1080p", "allowed": True}
    assert "items" not in remux


def test_transform_items_group():
    """Quality groups should have name, allowed, and items as string list."""
    result = transform_profile(SAMPLE_PROFILE)
    web = next(i for i in result["items"] if i["name"] == "WEB 1080p")
    assert web["allowed"] is True
    assert set(web["items"]) == {"WEBDL-1080p", "WEBRip-1080p"}


def test_transform_items_allowed_false():
    result = transform_profile(SAMPLE_PROFILE)
    unknown = next(i for i in result["items"] if i["name"] == "Unknown")
    assert unknown["allowed"] is False


def test_transform_preserves_score_fields():
    result = transform_profile(SAMPLE_PROFILE)
    assert result["minFormatScore"] == 0
    assert result["cutoffFormatScore"] == 10000
    assert result["minUpgradeFormatScore"] == 1
    assert result["upgradeAllowed"] is True


def test_transform_null_language():
    """arr API may return language as null — should default to 'Any'."""
    profile = {**SAMPLE_PROFILE, "language": None}
    result = transform_profile(profile)
    assert result["language"] == "Any"


def test_transform_null_format_items():
    """arr API may return formatItems as null instead of []."""
    profile = {**SAMPLE_PROFILE, "formatItems": None}
    result = transform_profile(profile)
    assert result["formatItems"] == {}


def test_transform_cutoff_not_found():
    """If cutoff ID not found in items, falls back to string of the int."""
    profile = {**SAMPLE_PROFILE, "cutoff": 9999}
    result = transform_profile(profile)
    assert result["cutoff"] == "9999"


def test_save_profile_creates_file(tmp_path):
    result = transform_profile(SAMPLE_PROFILE)
    save_profile(result, str(tmp_path))
    assert (tmp_path / "My Custom Profile.json").exists()


def test_save_profile_content(tmp_path):
    result = transform_profile(SAMPLE_PROFILE)
    save_profile(result, str(tmp_path))
    with open(tmp_path / "My Custom Profile.json") as f:
        data = json.load(f)
    assert data["name"] == "My Custom Profile"
    assert data["cutoff"] == "Remux-1080p"
    assert data["language"] == "Original"
    assert "id" not in data


def test_save_profile_sanitises_filename(tmp_path):
    profile = transform_profile({**SAMPLE_PROFILE, "name": 'Profile "test" / one'})
    save_profile(profile, str(tmp_path))
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert '"' not in files[0].name
    assert '/' not in files[0].name
