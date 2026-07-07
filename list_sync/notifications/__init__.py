"""
Notification modules for ListSync.
"""

from .discord import send_to_discord_webhook
from .telegram import send_to_telegram

__all__ = ['send_to_discord_webhook', 'send_to_telegram']
