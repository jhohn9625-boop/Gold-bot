import os
from threading import Thread
from flask import Flask

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

import os, yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# To avoid duplicate signal
last_signal = {"type": None}

def check_a_plus():
    try:
        data = yf.download("GC=F", period="2d", interval="30m", progress=False)
        if data.empty:
            return None, None
        
        # Last 2 candles for confirmation
        price = float(data['Close'].iloc[-1].item())
        prev_price = float(data['Close'].iloc[-2].item())
        low = float(data['Low'].iloc[-1].item())
        high = float(data['High'].iloc[-1].item())

        # === A+ RULES ===
        # 1. BUY A+: Price touch support 3975-3986 and bounce up
        if low <= 3986 and price > prev_price and price < 4000:
            # Check say e don bounce, no be still falling
            msg = f"""🏆 *A+ SETUP DON SHOW - BUY* 🟢

*Pair:* GOLD (XAUUSD)
*Live Price (Yahoo 30m):* ${price:.2f}
*Entry:* ${price:.2f} - ${price+4:.2f}
*Stop Loss:* ${price-12:.2f}
*TP1:* ${price+25:.2f}
*TP2:* ${price+45:.2f}

*Why na A+:*
✅ Price touch Support $3,982
✅ 30m candle show bounce (low ${low:.2f} -> close ${price:.2f})
✅ No be middle, na real zone

*For your $10 Demo:*
Lot: 0.01 ONLY
Risk: ~$0.12
If TP1 hit: +$0.25
If TP2 hit: +$0.45

No chase am if price don go far pass $4,000.
"""
            return "BUY", msg

        # 2. SELL A+: Price touch resistance 4008-4020 and reject down
        elif high >= 4008 and price < prev_price and price > 3985:
            msg = f"""🏆 *A+ SETUP DON SHOW - SELL* 🔴

*Pair:* GOLD (XAUUSD)
*Live Price (Yahoo 30m):* ${price:.2f}
*Entry:* ${price-4:.2f} - ${price:.2f}
*Stop Loss:* ${price+12:.2f}
*TP1:* ${price-25:.2f}
*TP2:* ${price-45:.2f}

*Why na A+:*
✅ Price touch Resistance $4,008
✅ 30m candle show rejection (high ${high:.2f} -> close ${price:.2f})
✅ No be middle, na real zone

*For your $10 Demo:*
Lot: 0.01 ONLY
Risk: ~$0.12
If TP1 hit: +$0.25

No chase am if price don fall far pass $3,985.
"""
            return "SELL", msg
        
        else:
            return None, None  # No A+, keep quiet
    except Exception as e:
        print(f"Error: {e}")
        return None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Welcome to A+ ONLY Bot! 🏆\nYour CHAT_ID: `{update.effective_chat.id}`\n\nI no go disturb you. I go only send when A+ setup show.\n\n/signal - Check Yahoo now (force check)\n/calc 3981 3965 4008 - Calc for $10\n/auto - Turn ON A+ auto alert",
        parse_mode="Markdown"
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sig_type, msg = check_a_plus()
    if msg:
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        # Manual check - tell price but say no A+
        try:
            data = yf.download("GC=F", period="1d", interval="30m", progress=False)
            price = float(data['Close'].iloc[-1].item())
            await update.message.reply_text(f"Gold now ${price:.2f}\nNo A+ yet. E dey middle. I go alert you when e reach zone. ⏳")
        except:
            await update.message.reply_text("Yahoo dey delay, try again.")

async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        entry = float(args[0]); sl = float(args[1]); tp = float(args[2])
        lot = float(args[3]) if len(args) > 3 else 0.01
        bal = float(args[4]) if len(args) > 4 else 10.0
        risk = abs(entry - sl) * (lot * 100)
        profit = abs(tp - entry) * (lot * 100)
        await update.message.reply_text(f"💰 TP: +${profit:.2f} ✅\nSL: -${risk:.2f} ❌\nRisk: {risk/bal*100:.1f}%", parse_mode="Markdown")
    except:
        await update.message.reply_text("Use: /calc 3981 3965 4008")

async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    global last_signal
    sig_type, msg = check_a_plus()
    # Only send if na new A+ and no be same as last one
    if msg and sig_type != last_signal["type"]:
        last_signal["type"] = sig_type
        if CHAT_ID:
            await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    # If no A+, do nothing - keep quiet

async def auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.job_queue.run_repeating(auto_job, interval=1800, first=5) # 1800 = 30mins
    await update.message.reply_text("✅ A+ Alert ON! I go only send you when A+ setup show. If no setup, I go keep quiet.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("calc", calc))
    app.add_handler(CommandHandler("auto", auto))
    print("A+ ONLY Bot don start...")
    app.run_polling()
