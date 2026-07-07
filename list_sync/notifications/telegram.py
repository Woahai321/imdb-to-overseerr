"""
Telegram Bot API notifications for ListSync.
"""

import logging
import os
import time
from html import escape
from typing import Any, Dict, Optional, Tuple

import requests

from ..ui.display import SyncResults
from .discord import (
    create_progress_bar,
    format_avg_time,
    format_time,
    get_list_emoji,
    get_percentage_text,
)

TELEGRAM_API_BASE_URL = "https://api.telegram.org"
TELEGRAM_REQUEST_TIMEOUT = 10


def get_telegram_config() -> Tuple[Optional[str], Optional[str]]:
    """
    Get Telegram bot token and chat ID from database config or environment.

    Returns:
        Tuple of (bot_token, chat_id); each may be None if not configured
    """
    # Try to load from ConfigManager/database first
    try:
        from ..config import ConfigManager

        config = ConfigManager()

        # Check if Telegram is enabled
        telegram_enabled = config.get_setting("telegram_enabled")
        if telegram_enabled and str(telegram_enabled).lower() in ("true", "1", "yes"):
            bot_token = config.get_setting("telegram_bot_token")
            chat_id = config.get_setting("telegram_chat_id")
            if bot_token and chat_id:
                return bot_token, chat_id
    except Exception as e:
        logging.debug(f"Could not load Telegram config from database: {e}")

    # Fallback to environment variables
    return os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> None:
    """
    Send a message to a Telegram chat via the Bot API.

    Args:
        bot_token: Telegram bot token from @BotFather
        chat_id: Target chat ID (user, group or channel)
        text: Message text with HTML formatting

    Raises:
        requests.exceptions.RequestException: If the Bot API request fails
    """
    url = f"{TELEGRAM_API_BASE_URL}/bot{bot_token}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=TELEGRAM_REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def send_to_telegram(
    summary_text: str,
    sync_results: SyncResults,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    automated: bool = False,
    is_single_list: bool = False,
) -> None:
    """Send sync summary notification to Telegram with rich context."""
    # Get credentials from parameters, database config, or environment
    if not bot_token or not chat_id:
        bot_token, chat_id = get_telegram_config()

    if not bot_token or not chat_id:
        return  # No Telegram configured

    # Double-check if Telegram is enabled in config
    try:
        from ..config import ConfigManager

        config = ConfigManager()
        telegram_enabled = config.get_setting("telegram_enabled")
        if telegram_enabled and str(telegram_enabled).lower() not in (
            "true",
            "1",
            "yes",
        ):
            return  # Telegram notifications disabled
    except Exception:
        # If we can't check config, proceed with credentials if provided
        pass

    try:
        enhanced_data = collect_enhanced_sync_data(
            sync_results, automated, is_single_list
        )
        message = build_summary_message(enhanced_data)
        send_telegram_message(bot_token, chat_id, message)
        logging.info("Telegram notification sent successfully")
    except Exception as e:
        logging.error(f"Failed to send Telegram notification: {str(e)}")


def collect_enhanced_sync_data(
    sync_results: SyncResults, automated: bool = False, is_single_list: bool = False
) -> Dict[str, Any]:
    """Collect data for enhanced notifications."""
    return {
        "sync_results": sync_results,
        "automated": automated,
        "is_single_list": is_single_list,
        "processing_time": time.time() - sync_results.start_time,
    }


def build_summary_message(data: Dict[str, Any]) -> str:
    """Build a comprehensive HTML-formatted summary message for Telegram."""
    sync_results = data["sync_results"]
    processing_time = data["processing_time"]

    total_items = sync_results.total_items or 1
    successful_items = (
        sync_results.results["requested"]
        + sync_results.results["already_available"]
        + sync_results.results["already_requested"]
        + sync_results.results["skipped"]
    )
    success_rate = (successful_items / total_items) * 100 if total_items > 0 else 0
    failed_items = sync_results.results["not_found"] + sync_results.results["error"]

    # Dynamic styling based on success rate
    if success_rate >= 95:
        status_emoji = "✨"
    elif success_rate >= 80:
        status_emoji = "✅"
    elif success_rate >= 60:
        status_emoji = "⚠️"
    else:
        status_emoji = "❌"

    # Build title with emoji
    if data.get("is_single_list", False):
        sync_mode = "📋 Single List"
        if sync_results.synced_lists:
            list_info = sync_results.synced_lists[0]
            list_type = list_info.get("type", "Unknown").upper()
            sync_mode = f"📋 {escape(list_type)} List"
    else:
        sync_mode = "🎬 Full Sync"

    movies = sync_results.media_type_counts["movie"]
    shows = sync_results.media_type_counts["tv"]

    lines = [
        f"{status_emoji} <b>{sync_mode} Complete</b>",
        "",
        f"{create_progress_bar(success_rate)} <b>{success_rate:.1f}%</b> Success Rate",
        (
            f"<b>{successful_items:,}</b> of <b>{total_items:,}</b> "
            "items processed successfully"
        ),
        f"⏱️ Completed in <b>{format_time(processing_time)}</b>",
        "",
        (
            f"🎬 Movies: <b>{movies:,}</b> ({get_percentage_text(movies, total_items)})"
            f" • 📺 TV Shows: <b>{shows:,}</b> "
            f"({get_percentage_text(shows, total_items)})"
        ),
        f"⚡ Speed: <b>{format_avg_time(processing_time, total_items)}</b> per item",
    ]

    # === RESULTS BREAKDOWN ===
    results_lines = []

    if sync_results.results["requested"] > 0:
        results_lines.append(
            f"✅ <b>{sync_results.results['requested']:,}</b> New Requests Sent"
        )

    if sync_results.results["already_available"] > 0:
        results_lines.append(
            f"💚 <b>{sync_results.results['already_available']:,}</b> Already Available"
        )

    if sync_results.results["already_requested"] > 0:
        results_lines.append(
            f"📌 <b>{sync_results.results['already_requested']:,}</b> Already Requested"
        )

    if sync_results.results["skipped"] > 0:
        results_lines.append(
            f"⏭️ <b>{sync_results.results['skipped']:,}</b> Skipped (Recent)"
        )

    if failed_items > 0:
        results_lines.append(f"❌ <b>{failed_items:,}</b> Failed")

    lines.append("")
    lines.append("<b>📊 Results Breakdown</b>")
    lines.append("\n".join(results_lines) if results_lines else "No items processed")

    # === SYNCED LISTS ===
    if sync_results.synced_lists:
        lists_lines = []
        for list_info in sync_results.synced_lists[:5]:
            list_type = list_info.get("type", "Unknown").upper()
            item_count = list_info.get("item_count", 0)
            list_url = list_info.get("url", "")

            list_emoji = get_list_emoji(list_type)

            if list_url and list_url.startswith(("http://", "https://")):
                lists_lines.append(
                    f'{list_emoji} <a href="{escape(list_url, quote=True)}">'
                    f"<b>{escape(list_type)}</b></a> — {item_count:,} items"
                )
            else:
                lists_lines.append(
                    f"{list_emoji} <b>{escape(list_type)}</b> — {item_count:,} items"
                )

        if len(sync_results.synced_lists) > 5:
            remaining = len(sync_results.synced_lists) - 5
            plural = "s" if remaining > 1 else ""
            lists_lines.append(f"<i>... and {remaining} more list{plural}</i>")

        lines.append("")
        lines.append("<b>📋 Synced Lists</b>")
        lines.append("\n".join(lists_lines))

    # === ERRORS (if any) ===
    if failed_items > 0 and sync_results.not_found_items:
        error_lines = []
        for item in sync_results.not_found_items[:3]:
            title = item.get("title", "Unknown")
            # Truncate long titles
            if len(title) > 40:
                title = title[:37] + "..."
            error_lines.append(f"• {escape(title)}")

        if len(sync_results.not_found_items) > 3:
            remaining = len(sync_results.not_found_items) - 3
            error_lines.append(f"<i>... and {remaining} more</i>")

        lines.append("")
        lines.append("<b>⚠️ Not Found</b>")
        lines.append("\n".join(error_lines))

    return "\n".join(lines)
