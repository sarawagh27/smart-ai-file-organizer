import json

import pytest

from smart_ai_file_organizer import main as cli


def _config(path):
    data = {
        "categories": ["Finance", "Other"],
        "training_data": {
            "Finance": ["invoice payment bank account tax revenue"],
            "Other": ["manual guide general notes"],
        },
        "organizer": {"supported_extensions": [".txt"], "fallback_category": "Other"},
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_cli_version_exits_successfully(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["smart-organizer", "--version"])

    with pytest.raises(SystemExit) as exc:
        cli.parse_args()

    assert exc.value.code == 0
    assert "smart-organizer" in capsys.readouterr().out


def test_cli_invalid_directory_returns_error(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["smart-organizer", str(tmp_path / "missing")])

    assert cli.main() == 1


def test_cli_invalid_config_returns_error(monkeypatch, tmp_path):
    bad_config = tmp_path / "bad.json"
    bad_config.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["smart-organizer", str(tmp_path), "--dry-run", "--config", str(bad_config)],
    )

    assert cli.main() == 1


def test_cli_dry_run_with_custom_config(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    _config(config_path)
    (tmp_path / "invoice.txt").write_text("invoice payment bank account tax revenue")
    monkeypatch.setattr(
        "sys.argv",
        ["smart-organizer", str(tmp_path), "--dry-run", "--config", str(config_path)],
    )

    assert cli.main() == 0
    assert not (tmp_path / ".smart-organizer" / "history.jsonl").exists()


# -- live-run confirmation ----------------------------------------------------

class _FakeTTY:
    def isatty(self):
        return True


class _NoTTY:
    def isatty(self):
        return False


def _live_args(tmp_path, *extra):
    config_path = tmp_path / "config.json"
    _config(config_path)
    (tmp_path / "invoice.txt").write_text("invoice payment bank account tax revenue")
    return ["smart-organizer", str(tmp_path), "--config", str(config_path), *extra]


def test_live_run_refused_when_not_interactive_and_no_yes(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", _live_args(tmp_path))
    monkeypatch.setattr("sys.stdin", _NoTTY())

    assert cli.main() == 2
    assert (tmp_path / "invoice.txt").exists()


def test_live_run_proceeds_with_yes(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", _live_args(tmp_path, "--yes"))

    assert cli.main() == 0
    assert not (tmp_path / "invoice.txt").exists()


def test_interactive_prompt_can_cancel_or_confirm(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.stdin", _FakeTTY())

    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
    monkeypatch.setattr("sys.argv", _live_args(tmp_path))
    assert cli.main() == 2
    assert (tmp_path / "invoice.txt").exists()

    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")
    assert cli.main() == 0
    assert not (tmp_path / "invoice.txt").exists()
