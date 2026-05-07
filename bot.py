
import os
import json
import time
import logging
from datetime import datetime

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler
)

# ==================================================
# CONFIG
# ==================================================

BOT_TOKEN = "8537711195:AAEJ72x1t2iWLLckZryL_hXb3U85mbeO_gw"
CHAT_ID = "1925437267"

EVENT_API = "https://jkt48.com/api/v1/exclusives?lang=id"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "stock_cache.json")
LOG_FILE = os.path.join(BASE_DIR, "history.log")
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")

CHECK_INTERVAL = 30

# ==================================================
# TARGET MEMBER
# ==================================================

def load_watchlist():

    if not os.path.exists(WATCHLIST_FILE):

        with open(WATCHLIST_FILE, "w") as f:
            json.dump([], f)

        return []

    try:

        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except:
        return []


def save_watchlist():

    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(TARGET_MEMBERS, f, indent=2, ensure_ascii=False)


TARGET_MEMBERS = load_watchlist()

# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==================================================
# VALIDASI
# ==================================================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN belum di set!")

if not CHAT_ID:
    raise ValueError("CHAT_ID belum di set!")

# ==================================================
# REQUEST SESSION
# ==================================================

session = requests.Session()

# ==================================================
# MEMORY
# ==================================================

last_sent = {}
last_notification_time = {}

# cooldown notif per member (detik)
NOTIFICATION_COOLDOWN = 60

# ==================================================
# CACHE FUNCTIONS
# ==================================================


def get_data_from_file():

    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        logging.error(f"Gagal baca cache: {e}")
        return {}



def save_data_to_file(data):

    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logging.error(f"Gagal simpan cache: {e}")


# ==================================================
# SAVE HISTORY LOG
# ==================================================


def save_history(text):

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    except Exception as e:
        logging.error(f"Gagal simpan history: {e}")


# ==================================================
# FETCH JSON
# ==================================================


def fetch_json(url):

    try:
        r = session.get(url, timeout=15)

        r.raise_for_status()

        return r.json()

    except requests.exceptions.RequestException as e:
        logging.error(f"REQUEST ERROR: {e}")
        return None


# ==================================================
# COMMANDS
# ==================================================

async def cek_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # CEK ARGUMENT
    if not context.args:

        await update.message.reply_text(
            "Gunakan:/cek Nama Member"
        )

        return

    # GABUNGKAN NAMA MEMBER
    target_name = " ".join(context.args).lower()

    data = fetch_json(EVENT_API)

    if not data:

        await update.message.reply_text(
            "❌ Gagal mengambil data API"
        )

        return

    events = data.get("data", [])

    hasil = []

    for event in events:

        try:

            event_code = event.get("code")

            if not event_code:
                continue

            category = event.get("category", "EVENT")

            detail_url = (
                f"https://jkt48.com/api/v1/exclusives/"
                f"{event_code}/bonus?lang=id"
            )

            detail_data = fetch_json(detail_url)

            if not detail_data:
                continue

            sessions = detail_data.get("data", [])

            for sess in sessions:

                label = sess.get("label", "Unknown")

                members = sess.get("session_members", [])

                for mb in members:

                    name = mb.get("member_name", "Unknown")

                    # COCOKKAN NAMA
                    if target_name in name.lower():

                        quota = int(mb.get("quota", 0))

                        hasil.append(
                            "━━━━━━━━━━━━━━\n"
                            f"👤 {name}\n"
                            f"📁 Kategori: {category}\n"
                            f"🎫 Sesi: {label}\n"
                            f"📦 Stok: {quota}\n"
                        )

        except Exception as e:
            logging.error(f"CEK COMMAND ERROR: {e}")

    # JIKA TIDAK ADA
    if not hasil:

        await update.message.reply_text(
            f"❌ Member tidak ditemukan: {target_name}"
        )

        return

    # BATASI PANJANG PESAN
    final_msg = "\n\n".join(hasil[:10])


    await update.message.reply_text(final_msg)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = (
        "🤖 JKT48 Stock Bot Aktif\n\n"
        "Commands:\n"
        "/status - Status bot\n"
        "/members - List oshimen monitor\n"
        "/cek Nama Member - Cek stok member\n"
        "/watch Nama Member - Tambah watchlist\n"
        "/unwatch Nama Member - Hapus watchlist"
        )

    await update.message.reply_text(msg)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cache = get_data_from_file()

    msg = (
    "🤖 JKT48 Stock Bot Aktif\n\n"
    )

    await update.message.reply_text(msg)


async def members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = "🎯 TARGET MEMBER\n\n"

    for member in TARGET_MEMBERS:
        msg += f"• {member}\n"

    await update.message.reply_text(msg)

async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "Gunakan:\n/watch Nama Member"
        )

        return

    member_name = " ".join(context.args)

    # CEK DUPLIKAT
    if member_name in TARGET_MEMBERS:

        await update.message.reply_text(
            f"⚠️ {member_name} sudah ada di watchlist"
        )

        return

    TARGET_MEMBERS.append(member_name)

    save_watchlist()

    await update.message.reply_text(
        f"✅ Added to watchlist:\n{member_name}"
    )


async def unwatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "Gunakan:\n/unwatch Nama Member"
        )

        return

    member_name = " ".join(context.args)

    # CEK ADA / TIDAK
    if member_name not in TARGET_MEMBERS:

        await update.message.reply_text(
            f"❌ {member_name} tidak ada di watchlist"
        )

        return

    TARGET_MEMBERS.remove(member_name)

    save_watchlist()

    await update.message.reply_text(
        f"🗑 Removed from watchlist:\n{member_name}"
    )


# ==================================================
# MONITOR STOCK
# ==================================================


async def monitor_stock(context: ContextTypes.DEFAULT_TYPE):

    logging.info("🔍 Mengecek stok terbaru...")

    current_cache = get_data_from_file()

    data = fetch_json(EVENT_API)

    if not data:
        return

    events = data.get("data", [])

    for event in events:

        try:

            event_code = event.get("code")

            if not event_code:
                continue

            category = event.get("category", "EVENT")

            detail_url = (
                f"https://jkt48.com/api/v1/exclusives/"
                f"{event_code}/bonus?lang=id"
            )

            detail_data = fetch_json(detail_url)

            if not detail_data:
                continue

            sessions = detail_data.get("data", [])

            for sess in sessions:

                label = sess.get("label", "Unknown")

                members = sess.get("session_members", [])

                for mb in members:

                    try:

                        name = mb.get("member_name", "Unknown")

                        # FILTER MEMBER
                        if TARGET_MEMBERS:
                            if name not in TARGET_MEMBERS:
                                continue

                        quota = int(mb.get("quota", 0))

                        key = (
                            f"{category}|||"
                            f"{event_code}|||"
                            f"{name}|||"
                            f"{label}"
                        )

                        old_quota = current_cache.get(key)

                        # PERTAMA KALI
                        if old_quota is None:

                            current_cache[key] = quota
                            save_data_to_file(current_cache)
                            continue

                        old_quota = int(old_quota)

                        # JIKA BERUBAH
                        if quota != old_quota:

                            notif_key = f"{key}_{quota}"

                            # ANTI DUPLICATE
                            if last_sent.get(notif_key):
                                continue

                            # COOLDOWN
                            now_time = time.time()

                            last_time = last_notification_time.get(key, 0)

                            if now_time - last_time < NOTIFICATION_COOLDOWN:
                                continue

                            last_notification_time[key] = now_time

                            last_sent[notif_key] = True

                            # UPDATE CACHE
                            current_cache[key] = quota

                            save_data_to_file(current_cache)

                            # STATUS
                            status = (
                                "📉 BELI"
                                if quota < old_quota
                                else "🔄 RESTOCK"
                            )

                            # SOLD OUT
                            if quota == 0:
                                status = "❌ SOLD OUT"

                            # RESTOCK BESAR
                            if old_quota == 0 and quota >= 5:
                                status = "🚨 RESTOCK BESAR"

                            # HAMPIR HABIS
                            if quota <= 2 and quota > 0:
                                status += "\n⚠️ STOK MENIPIS"

                            now = datetime.now().strftime("%H:%M:%S")

                            msg = (
                                f"{status}\n\n"
                                f"Member   : {name}\n"
                                f"Sesi     : {label}\n"
                                f"Stok     : {old_quota} → {quota}\n"
                                f"Kategori : {category}\n"
                                f"Waktu    : {now}"
                            )

                            logging.info(
                                f"STOK BERUBAH | "
                                f"{name} | "
                                f"{old_quota} -> {quota}"
                            )

                            # SAVE HISTORY
                            save_history(
                                f"[{now}] {name} | {old_quota} -> {quota}"
                            )

                            # KIRIM TELEGRAM
                            await context.bot.send_message(
                                chat_id=CHAT_ID,
                                text=msg
                            )

                    except Exception as e:
                        logging.error(
                            f"Gagal proses member: {e}"
                        )

        except Exception as e:
            logging.error(
                f"Gagal proses event "
                f"{event.get('code')}: {e}"
            )

    save_data_to_file(current_cache)


# ==================================================
# MAIN
# ==================================================


def main():

    if not os.path.exists(CACHE_FILE):
        save_data_to_file({})

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # COMMANDS
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("members", members_command))
    app.add_handler(CommandHandler("cek", cek_command))
    app.add_handler(CommandHandler("watch", watch_command))
    app.add_handler(CommandHandler("unwatch", unwatch_command))


    # JOB
    if app.job_queue:

        app.job_queue.run_repeating(
            monitor_stock,
            interval=CHECK_INTERVAL,
            first=5
        )

    logging.info("🚀 BOT AKTIF")
    logging.info(f"📁 Cache: {CACHE_FILE}")

    app.run_polling()


# ==================================================
# START
# ==================================================

if __name__ == "__main__":
    main()

