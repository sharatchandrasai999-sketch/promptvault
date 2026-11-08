"""Tests for promptvault. The store is isolated per test via tmp_path."""

import json

import pytest

from promptvault.cli import main
from promptvault.mock import mock_reply
from promptvault.store import get_version, list_prompts, list_versions, save_prompt


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Point the default store at a fresh temp dir for each test."""
    monkeypatch.setenv("PROMPTVAULT_STORE", str(tmp_path / "store"))
    return tmp_path / "store"


def test_save_creates_version_1_then_2(store):
    assert save_prompt(store, "greet", "Reply in uppercase.") == 1
    assert save_prompt(store, "greet", "Reply normally.") == 2
    versions = list_versions(store, "greet")
    assert [v["version"] for v in versions] == [1, 2]
    assert versions[0]["text"] == "Reply in uppercase."
    assert versions[1]["text"] == "Reply normally."


def test_list_shows_saved_prompts(store, capsys):
    save_prompt(store, "greet", "Reply in uppercase.")
    save_prompt(store, "greet", "Reply normally.")
    save_prompt(store, "summarize", "Summarize this.")
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "greet: 2 version(s)" in out
    assert "summarize: 1 version(s)" in out


def test_list_name_shows_versions(store, capsys):
    save_prompt(store, "greet", "Reply in uppercase.")
    assert main(["list", "--name", "greet"]) == 0
    out = capsys.readouterr().out
    assert "greet: 1 version(s)" in out
    assert "v1" in out
    assert "Reply in uppercase." in out


def test_mock_reply_keyword_rules():
    assert mock_reply("Reply in uppercase.", "hello") == "HELLO"
    assert mock_reply("Reply in lowercase.", "HELLO") == "hello"
    assert mock_reply("Please reverse it.", "abc") == "cba"
    assert mock_reply("Reply normally.", "hello") == "hello"


def _write_testset(path):
    path.write_text(
        json.dumps(
            [
                {"input": "hello", "expected": "HELLO"},
                {"input": "world", "expected": "WORLD"},
                {"input": "abc", "expected": "ABC"},
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_ab_picks_version_matching_expected(store, tmp_path, capsys):
    save_prompt(store, "greet", "Reply in uppercase.")
    save_prompt(store, "greet", "Reply normally.")
    testset = _write_testset(tmp_path / "testset.json")
    assert main(["ab", "--name", "greet", "--v1", "1", "--v2", "2",
                 "--testset", str(testset)]) == 0
    out = capsys.readouterr().out
    assert "v1: accuracy 100%" in out
    assert "v2: accuracy 0%" in out
    assert "Winner: v1" in out


def test_ab_missing_prompt_errors_cleanly(store, tmp_path, capsys):
    testset = _write_testset(tmp_path / "testset.json")
    assert main(["ab", "--name", "nope", "--v1", "1", "--v2", "2",
                 "--testset", str(testset)]) == 2
    err = capsys.readouterr().err
    assert "error:" in err
    assert "nope" in err


def test_ab_missing_version_errors_cleanly(store, tmp_path, capsys):
    save_prompt(store, "greet", "Reply in uppercase.")
    testset = _write_testset(tmp_path / "testset.json")
    assert main(["ab", "--name", "greet", "--v1", "1", "--v2", "9",
                 "--testset", str(testset)]) == 2
    assert "error:" in capsys.readouterr().err


def test_save_cli_prints_version(store, capsys):
    assert main(["save", "--name", "greet", "--text", "Reply in uppercase."]) == 0
    assert "Saved 'greet' version 1" in capsys.readouterr().out
    assert get_version(store, "greet", 1)["text"] == "Reply in uppercase."


def test_store_flag_overrides_env(store, tmp_path, capsys):
    other = tmp_path / "elsewhere"
    assert main(["--store", str(other), "save", "--name", "x", "--text", "hi"]) == 0
    assert list_prompts(store) == []  # env store untouched
    assert list_prompts(other) == [("x", 1)]
