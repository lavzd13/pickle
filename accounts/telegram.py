import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(text, reply_markup=None):
    """Send a message to the configured Telegram chat. Silently fails if not configured."""
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        logger.warning('Telegram not configured (TELEGRAM_TOKEN or TELEGRAM_CHAT_ID missing)')
        return

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.ok:
            logger.error('Telegram API error: %s', resp.text)
    except Exception:
        logger.exception('Failed to send Telegram message')


def _truncate_wallet(address):
    """Show first 6 and last 4 characters of a wallet address."""
    if len(address) <= 14:
        return address
    return f"{address[:6]}...{address[-4:]}"


def notify_deposit_order(order):
    """Send Telegram notification for a new deposit order."""
    network_name = order.network.name if order.network else '—'
    raw_wallet = order.wallet_address or ''
    balance = order.current_balance if order.current_balance is not None else '—'
    reply_markup = None

    if raw_wallet:
        reply_markup = {
            'inline_keyboard': [[
                {'text': _truncate_wallet(raw_wallet), 'copy_text': {'text': raw_wallet}}
            ]]
        }

    text = (
        f"\u200b━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔴 <b>New Deposit Order</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Account: <b>{order.account.nick}</b>\n"
        f"🎮 Platform: <b>{order.account.platform.name if order.account.platform else '—'}</b>\n"
        f"🌐 Network: <b>{network_name}</b>\n"
        f"💰 Current Balance: <b>{balance}</b>\n"
        f"📝 Ordered by: <b>{order.created_by.username if order.created_by else '—'}</b>\n"
        f"🕐 Time: <b>{order.created_at.strftime('%Y-%m-%d %H:%M')}</b>"
    )
    send_telegram_message(text, reply_markup=reply_markup)


def notify_withdrawal_order(order):
    """Send Telegram notification for a new withdrawal order."""
    balance = order.current_balance if order.current_balance is not None else '—'

    text = (
        f"\u200b━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>New Withdrawal Order</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Account: <b>{order.account.nick}</b>\n"
        f"🎮 Platform: <b>{order.account.platform.name if order.account.platform else '—'}</b>\n"
        f"💰 Current Balance: <b>{balance}</b>\n"
        f"📝 Ordered by: <b>{order.created_by.username if order.created_by else '—'}</b>\n"
        f"🕐 Time: <b>{order.created_at.strftime('%Y-%m-%d %H:%M')}</b>"
    )
    send_telegram_message(text)
