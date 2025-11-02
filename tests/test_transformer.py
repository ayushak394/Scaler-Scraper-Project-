import json
from src.transformer import transform_issue

def make_raw():
    return {
        "key": "TEST-1",
        "fields": {
            "summary": "Test issue",
            "project": {"key": "TEST"},
            "issuetype": {"name": "Bug"},
            "status": {"name": "Open"},
            "reporter": {"displayName": "Reporter One"},
            "description": "<p>This is a test</p>",
            "comment": {"comments": [{"author": {"displayName":"A"}, "body": "<p>c</p>", "created":"2020"}]}
        }
    }

def test_transform_issue():
    raw = make_raw()
    out = transform_issue(raw)
    assert out["id"] == "TEST-1"
    assert out["title"] == "Test issue"
    assert out["derived"]["classification_label"] == "Bug"
