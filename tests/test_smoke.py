import os
import json

def test_agents_md_exists():
    assert os.path.exists("AGENTS.md")

def test_features_json_valid():
    with open(".forge/projects/current/features.json") as f:
        data = json.load(f)
    assert "features" in data
