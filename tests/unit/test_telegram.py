"""Unit tests for Telegram notifications."""

from unittest.mock import Mock, patch

import pytest

from list_sync.notifications.telegram import (
    build_summary_message,
    collect_enhanced_sync_data,
    get_telegram_config,
    send_telegram_message,
    send_to_telegram,
)
from list_sync.ui.display import SyncResults


def make_sync_results() -> SyncResults:
    """Build a populated SyncResults instance for message tests."""
    sync_results = SyncResults()
    sync_results.total_items = 10
    sync_results.results["requested"] = 5
    sync_results.results["already_available"] = 2
    sync_results.results["already_requested"] = 1
    sync_results.results["skipped"] = 1
    sync_results.results["not_found"] = 1
    sync_results.media_type_counts = {"movie": 6, "tv": 4}
    sync_results.synced_lists = [
        {"type": "imdb", "item_count": 10, "url": "https://www.imdb.com/chart/top/"}
    ]
    sync_results.not_found_items = [{"title": "Some <Unmatched> Movie"}]
    return sync_results


class TestGetTelegramConfig:
    """Tests for Telegram credential resolution."""

    @patch("list_sync.config.ConfigManager", side_effect=Exception("no database"))
    def test_falls_back_to_environment(self, mock_config, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")

        assert get_telegram_config() == ("123:abc", "-100999")

    @patch("list_sync.config.ConfigManager", side_effect=Exception("no database"))
    def test_returns_none_when_unconfigured(self, mock_config, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

        assert get_telegram_config() == (None, None)

    def test_reads_from_database_when_enabled(self):
        mock_manager = Mock()
        mock_manager.get_setting.side_effect = lambda key: {
            "telegram_enabled": "true",
            "telegram_bot_token": "db-token",
            "telegram_chat_id": "db-chat",
        }[key]

        with patch("list_sync.config.ConfigManager", return_value=mock_manager):
            assert get_telegram_config() == ("db-token", "db-chat")


class TestSendTelegramMessage:
    """Tests for the Bot API request."""

    @patch("list_sync.notifications.telegram.requests.post")
    def test_sends_expected_payload(self, mock_post):
        mock_post.return_value = Mock(status_code=200)

        send_telegram_message("123:abc", "-100999", "<b>hello</b>")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.telegram.org/bot123:abc/sendMessage"
        assert kwargs["json"]["chat_id"] == "-100999"
        assert kwargs["json"]["text"] == "<b>hello</b>"
        assert kwargs["json"]["parse_mode"] == "HTML"

    @patch("list_sync.notifications.telegram.requests.post")
    def test_raises_on_api_error(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="401"):
            send_telegram_message("bad-token", "-100999", "hello")


class TestSendToTelegram:
    """Tests for the notification entry point."""

    @patch("list_sync.notifications.telegram.send_telegram_message")
    @patch(
        "list_sync.notifications.telegram.get_telegram_config",
        return_value=(None, None),
    )
    def test_skips_when_not_configured(self, mock_config, mock_send):
        send_to_telegram("summary", make_sync_results())

        mock_send.assert_not_called()

    @patch("list_sync.config.ConfigManager", side_effect=Exception("no database"))
    @patch("list_sync.notifications.telegram.send_telegram_message")
    def test_sends_with_explicit_credentials(self, mock_send, mock_config):
        send_to_telegram(
            "summary",
            make_sync_results(),
            bot_token="123:abc",
            chat_id="-100999",
        )

        mock_send.assert_called_once()
        bot_token, chat_id, message = mock_send.call_args[0]
        assert bot_token == "123:abc"
        assert chat_id == "-100999"
        assert "Full Sync" in message

    @patch("list_sync.config.ConfigManager", side_effect=Exception("no database"))
    @patch(
        "list_sync.notifications.telegram.send_telegram_message",
        side_effect=Exception("network down"),
    )
    def test_swallows_send_errors(self, mock_send, mock_config):
        # Notification failures must never break the sync flow
        send_to_telegram(
            "summary",
            make_sync_results(),
            bot_token="123:abc",
            chat_id="-100999",
        )


class TestBuildSummaryMessage:
    """Tests for the HTML summary message."""

    @pytest.fixture
    def message(self):
        data = collect_enhanced_sync_data(make_sync_results())
        return build_summary_message(data)

    def test_includes_success_rate_and_totals(self, message):
        assert "90.0%" in message
        assert "<b>9</b> of <b>10</b>" in message

    def test_includes_results_breakdown(self, message):
        assert "<b>5</b> New Requests Sent" in message
        assert "<b>2</b> Already Available" in message
        assert "<b>1</b> Failed" in message

    def test_includes_synced_lists_with_link(self, message):
        assert '<a href="https://www.imdb.com/chart/top/">' in message
        assert "<b>IMDB</b>" in message

    def test_escapes_html_in_titles(self, message):
        assert "Some <Unmatched> Movie" not in message
        assert "Some &lt;Unmatched&gt; Movie" in message

    def test_single_list_mode_title(self):
        data = collect_enhanced_sync_data(
            make_sync_results(), automated=True, is_single_list=True
        )
        message = build_summary_message(data)
        assert "IMDB List Complete" in message
