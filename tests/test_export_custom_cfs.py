"""Tests for export-custom-cfs.py"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from export_custom_cfs import extract_trash_names, save_cf
import tempfile
import json


SAMPLE_YML = """
sonarr:
  series:
    base_url: http://example.com:8989
    api_key: abc123
    custom_formats:
      - trash_ids:
          - f67c9ca88f463a48346062e8ad07713f # ATVP
          - d9e511921c8cedc7282e291b0209cdc5 # ATV
          - 505d871304820ba7106b693be6fe4a9e # HDR
          - 0d7824bb924701997f874e7ff7d4844a # TrueHD ATMOS

radarr:
  movies:
    base_url: http://example.com:7878
    api_key: def456
    custom_formats:
      - trash_ids:
          - 957d0f44b592285f26449575e8b1167e # Special Edition
          - eecf3a857724171f968a66cb5719e152 # IMAX
"""


@pytest.fixture
def recyclarr_yml(tmp_path):
    f = tmp_path / "recyclarr.yml"
    f.write_text(SAMPLE_YML)
    return str(f)


def test_extract_trash_names_sonarr(recyclarr_yml):
    names = extract_trash_names(recyclarr_yml)
    assert "atvp" in names["sonarr"]
    assert "atv" in names["sonarr"]
    assert "hdr" in names["sonarr"]
    assert "truehd atmos" in names["sonarr"]

def test_extract_trash_names_radarr(recyclarr_yml):
    names = extract_trash_names(recyclarr_yml)
    assert "special edition" in names["radarr"]
    assert "imax" in names["radarr"]

def test_extract_trash_names_lowercase(recyclarr_yml):
    names = extract_trash_names(recyclarr_yml)
    # All names must be lowercase for case-insensitive matching
    for arr_type in ("sonarr", "radarr"):
        for name in names[arr_type]:
            assert name == name.lower()

def test_extract_trash_names_no_crossover(recyclarr_yml):
    names = extract_trash_names(recyclarr_yml)
    # Sonarr names shouldn't appear in radarr and vice versa
    assert "atvp" not in names["radarr"]
    assert "special edition" not in names["sonarr"]

def test_extract_trash_names_empty_section():
    yml = "sonarr:\nradarr:\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(yml)
        path = f.name
    try:
        names = extract_trash_names(path)
        assert names["sonarr"] == set()
        assert names["radarr"] == set()
    finally:
        os.unlink(path)

def test_save_cf_creates_file(tmp_path):
    cf = {"name": "My Custom CF", "id": 1, "specifications": []}
    save_cf(cf, str(tmp_path))
    assert (tmp_path / "My Custom CF.json").exists()

def test_save_cf_sanitises_filename(tmp_path):
    cf = {"name": 'CF with "quotes" and /slashes\\', "id": 2}
    save_cf(cf, str(tmp_path))
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert '"' not in files[0].name
    assert '/' not in files[0].name

def test_save_cf_content(tmp_path):
    cf = {"name": "TestCF", "id": 42, "specifications": [{"name": "spec1"}]}
    save_cf(cf, str(tmp_path))
    with open(tmp_path / "TestCF.json") as f:
        data = json.load(f)
    assert data["name"] == "TestCF"
    assert data["specifications"] == [{"name": "spec1"}]

def test_save_cf_strips_id(tmp_path):
    cf = {"name": "TestCF", "id": 42}
    save_cf(cf, str(tmp_path))
    with open(tmp_path / "TestCF.json") as f:
        data = json.load(f)
    assert "id" not in data
