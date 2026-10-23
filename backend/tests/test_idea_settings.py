import pytest
from pydantic import ValidationError

from app.modules.ideas.settings import IdeaSettings


def test_limits_read_server_dotenv_and_environment_wins(tmp_path, monkeypatch):
    monkeypatch.delenv("IDEAS_DAILY_LIMIT", raising=False)
    file = tmp_path / ".env"
    file.write_text(
        "IDEAS_DAILY_LIMIT=4\nIDEAS_SUGGESTIONS_DAILY_LIMIT=7\nIDEAS_REPORTS_DAILY_LIMIT=3\n",
        encoding="utf-8",
    )
    loaded = IdeaSettings(_env_file=file)
    assert loaded.ideas_daily_limit == 4
    assert loaded.ideas_suggestions_daily_limit == 7
    assert loaded.ideas_reports_daily_limit == 3
    monkeypatch.setenv("IDEAS_DAILY_LIMIT", "2")
    assert IdeaSettings(_env_file=file).ideas_daily_limit == 2


@pytest.mark.parametrize("limit", ["0", "-1", "1001", "garbage"])
def test_invalid_limits_are_rejected(limit, monkeypatch):
    monkeypatch.setenv("IDEAS_DAILY_LIMIT", limit)
    with pytest.raises(ValidationError):
        IdeaSettings(_env_file=None)
