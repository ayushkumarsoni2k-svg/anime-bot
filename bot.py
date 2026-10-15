import os
import json
import random
import asyncio
import requests
import urllib.parse
import xml.etree.ElementTree as ET
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# PIL Antialias Fix for MoviePy compatibility
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

def get_live_anime_trends():
    """Step 1: Fetch a completely random page of anime from Jikan API to ensure 100% unique topics every time."""
    anime_data_list = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    random_page = random.randint(1, 40)
    
    for attempt in range(3):
        try:
            url = f"https://api.jikan.moe/v4/anime?page={random_page}&limit=25&sfw=true"
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                for item in items:
                    title = item.get("title", "Anime")
                    synopsis = item.get("synopsis", "An epic journey.")[:150]
                    anime_data_list.append(f"Anime: {title} | Details: {synopsis}")
                if anime_data_list:
                    print(f"✅ Jikan API से पेज {random_page} के ताज़ा रैंडम एनीमे मिल गए!")
                    break
        except Exception as e:
            print(f"Jikan API attempt {attempt+1} failed: {e}")
            import time
            time.sleep(2)
            
    if not anime_data_list:
        print("⚠️ Jikan API व्यस्त है, Google News RSS से लाइव ट्रेंड्स खोजे जा रहे हैं...")
        try:
            keywords = ["trending anime action", "secret anime lore 2026", "powerful anime characters", "dark fantasy anime twists"]
            selected_keyword = random.choice(keywords)
            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(selected_keyword)}&hl=en-IN&gl=IN&ceid=IN:en"
            res = requests.get(rss_url, headers=headers, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.text)
                for item in root.findall('.//item')[:15]:
                    title_elem = item.find('title')
                    if title_elem is not None and title_elem.text:
                        anime_data_list.append(f"Anime News/Trend: {title_elem.text}")
                if anime_data_list:
                    print("✅ Google News RSS से लाइव ट्रेंड्स मिल गए!")
        except Exception as e:
            print(f"Google News RSS failed: {e}")

    if not anime_data_list:
        anime_data_list = [
            "Anime: Solo Leveling Season 2 | Details: Jinwoo's shadow army rises in epic battles.",
            "Anime: Jujutsu Kaisen | Details: Sorcerers fighting curses in intense action sequences.",
            "Anime: Demon Slayer | Details: Hashira training and fierce battles against upper moons.",
            "Anime: Chainsaw Man | Details: Denji's chaotic life as a devil hunter in a dark world.",
            "Anime: Bleach Thousand-Year Blood War | Details: Soul Reapers facing their ultimate doom."
        ]
        
    random.shuffle(anime_data_list)
    return "\n".join(anime_data_list)

def generate_script_with_gemini(live_trends):
    """Step 2: Send randomized trends with a random seed to Gemini API to get a 100% fresh, unique script and angle every time."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("❌ GEMINI_API_KEY GitHub Secrets में नहीं मिली!")
        
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    unique_seed = random.randint(10000, 99999)
    
    prompt = (
        f"Randomization Salt: {unique_seed}\n"
        "You are a viral Hindi/Hinglish Anime YouTube Shorts creator.\n"
        "Here is a randomized list of current live anime topics:\n"
        f"{live_trends}\n\n"
        "Instructions:\n"
        "1. Pick ONE anime topic from this list. Even if the anime name is similar to a previous one, you MUST write a completely fresh, unique storytelling angle (e.g., focus on hidden secrets, dark lore, unexpected plot twists, or epic character awakenings).\n"
        "2. Write a strict 4 to 5-scene dramatic Hindi/Hinglish script for a 1-minute short video.\n"
        "3. For each scene, provide:\n"
        "   - 'narration': The Hindi/Hinglish voiceover line (12-15 words) using deep narration style.\n"
        "   - 'subtitle': Short, crisp Hinglish text for screen subtitles (Roman Hindi matching the narration).\n"
        "   - 'video_prompt': A detailed 8-second AI video generation prompt in English describing camera motion and cinematic anime visuals.\n\n"
        "Return ONLY valid JSON format matching this exact structure, with no extra text or markdown blocks:\n"
        "{\n"
        '  "title": "Catchy Anime Title ⚡ #shorts #anime",\n'
        '  "scenes": [\n'
        '    {\n'
        '      "narration": "...",\n'
        '      "subtitle": "...",\n'
        '      "video_prompt": "..."\n'
        '    }\n'
        '  ]\n'
        "}"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(3):
        try:
            res = requests.post(gemini_url, json=payload, headers=headers, timeout=20)
            if res.status_code == 200:
                result_json = res.json()
                candidate_text = result_json['candidates'][0]['content']['parts'][0]['text']
                clean_text = candidate_text.replace("```json", "").replace("```", "").strip()
                script_data = json.loads(clean_text)
                print("✅ Gemini API से बिल्कुल नया यूनिक एंगल वाला स्क्रिप्ट बन गया!")
                return script_data
        except Exception as e:
            print(f"Gemini API attempt {attempt+1} failed: {e}")
            
    return {
        "title": "Epic Anime Moment 🔥 #shorts",
        "scenes": [
            {"narration": "साल 2026 में एनीमी की दुनिया में भूचाल आ गया है!", "subtitle": "Saal 2026 mein anime ki duniya mein bhuchaal aa gaya hai!", "video_prompt": "Cinematic 8-second anime motion video clip, epic key visual, dynamic camera zoom."},
            {"narration": "हर कोई इस जबरदस्त और खतरनाक मोड़ को देखकर हैरान है!", "subtitle": "Har koi is zabardast aur khatarnak mod ko dekhkar hairaan hai!", "video_prompt": "Intense 8-second anime battle action, vibrant colors, fast-paced camera panning."},
            {"narration": "इस कैरेक्टर की ताकत ने पूरी दुनिया को पीछे छोड़ दिया है!", "subtitle": "Is character ki taakat ne poori duniya ko peeche chhod diya hai!", "video_prompt": "Mysterious dark anime character standing with immense power, moody lighting."},
            {"narration": "क्या होने वाला है आगे? कमेंट में जरूर बताएं!", "subtitle": "Kya hone wala hai aage? Comment mein zaroor batayein!", "video_prompt": "Epic anime hero looking at a breathtaking horizon, sunset glow, smooth cinematic camera push-in."}
        ]
    }

async def make_deep_voice(text, filename):
    """Step 3: Generate deep Hindi voiceover using Edge TTS"""
    communicate = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural", rate="+5%", pitch="-8Hz")
    await communicate.save(filename)

async def build_video(script):
    """Step 4: Download images, burn Hinglish subtitles directly onto frames using PIL, add zoom effect, and concatenate scenes"""
    clips = []
    scenes = script.get("scenes", [])
    
    # Try loading a bold system font for subtitles, fallback to default if not found
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, 34)
    except Exception:
        font = ImageFont.load_default()

    for i, scene in enumerate(scenes):
        narration_text = scene.get("narration", "Anime Trend")
        subtitle_text = scene.get("subtitle", narration_text)
        vid_prompt = scene.get("video_prompt", "anime masterpiece")
        
        aud_file = f"scene_{i}.mp3"
        img_file = f"scene_{i}.jpg"
        
        print(f"🎬 प्रोसेसिंग सीन {i+1}...")
        
        await make_deep_voice(narration_text, aud_file)
        audio_clip = AudioFileClip(aud_file)
        
        image_saved = False
        try:
            encoded_prompt = urllib.parse.quote(vid_prompt + ", high quality anime wallpaper")
            seed_num = random.randint(100, 99999)
            img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&seed={seed_num}&nologo=true"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            
            res = requests.get(img_url, headers=headers, timeout=20)
            if res.status_code == 200 and len(res.content) > 1000:
                with open(img_file, "wb") as f:
                    f.write(res.content)
                with Image.open(img_file) as test_img:
                    test_img.verify()
                image_saved = True
        except Exception as e:
            print(f"Image download error for scene {i}: {e}")
            
        if not image_saved:
            print(f"⚠️ Local fail-safe dark anime image generate ki ja rahi hai scene {i} ke liye...")
            img = Image.new("RGB", (720, 1280), color=(12, 12, 25))
            draw = ImageDraw.Draw(img)
            draw.rectangle([30, 30, 690, 1250], outline=(100, 100, 220), width=4)
            draw.text((60, 600), f"SCENE {i+1} ANIME", fill=(220, 220, 255))
            img.save(img_file)
                
        # 3. Process image, add subtitle overlay directly onto the frame, and add zoom effect
        base_img = Image.open(img_file).convert("RGB")
        base_img = base_img.resize((720, 1280))
        
        # Burn-in Subtitle on Image using PIL
        draw = ImageDraw.Draw(base_img)
        # Draw semi-transparent background box at bottom for subtitle readability
        draw.rectangle([40, 1080, 680, 1210], fill=(0, 0, 0))
        draw.rectangle([40, 1080, 680, 1210], outline=(255, 255, 255), width=2)
        
        # Text wrapping for subtitle
        words = subtitle_text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + " " + word) < 38:
                current_line = (current_line + " " + word).strip()
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
            
        y_text = 1100
        for line in lines[:2]: # Max 2 lines
            draw.text((60, y_text), line, fill=(255, 255, 0)) # Bright yellow text for subtitles
            y_text += 45
            
        base_img.save(img_file)
        
        dur = audio_clip.duration + 0.3
        img_clip = ImageClip(img_file).set_duration(dur)
        zoom_clip = img_clip.resize(lambda t: 1 + 0.03 * (t / dur))
        video_scene = zoom_clip.set_audio(audio_clip)
        clips.append(video_scene)
        
    print("🔄 सभी सीन्स को जोड़ा जा रहा है...")
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile("Ready_Anime_Short.mp4", fps=24, codec="libx264", audio_codec="aac")
    
    with open("Video_Title.txt", "w", encoding="utf-8") as f:
        f.write(script.get("title", "Trending Anime Short"))
        
    print("✅ शानदार शॉर्ट वीडियो सबटाइटल के साथ सफलतापूर्वक बन गया!")

def send_email_notification(script):
    """Step 5: Send the generated video and full scene-by-scene video generation prompts with Hinglish subtitles directly to your Gmail"""
    try:
        sender_email = os.environ.get("MY_GMAIL")
        sender_password = os.environ.get("GMAIL_APP_PASS")
        
        if not sender_email or not sender_password:
            print("⚠️ MY_GMAIL या GMAIL_APP_PASS GitHub Secrets में नहीं मिले, ईमेल भेजना छोड़ दिया जा रहा है।")
            return

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = sender_email
        
        title = script.get("title", "Trending Anime Short")
        msg['Subject'] = f"🎬 New Unique Anime Short Ready: {title}"

        body = (
            "नमस्ते!\n\n"
            "आपका बिल्कुल नए और यूनिक एंगल पर आधारित ऑटोमैटिक एनिमी शॉर्ट वीडियो तैयार हो गया है (सबटाइटल के साथ)!\n"
            f"📌 वीडियो शीर्षक (Title): {title}\n\n"
            "--------------------------------------------------\n"
            "📱 मोबाइल से मैनुअल वीडियो बनाने के लिए सीन-बाय-सीन वीडियो प्रॉम्प्ट्स (हिन्ग्लिश सबटाइटल सहित):\n"
            "--------------------------------------------------\n"
        )
        
        for i, scene in enumerate(script.get("scenes", [])):
            body += (
                f"\n[सीन {i+1} - लगभग 8 सेकंड]\n"
                f"🎙️ वॉयसओवर नैरेशन (Voiceover): {scene.get('narration')}\n"
                f"💬 हिन्ग्लिश सबटाइटल (Subtitle): {scene.get('subtitle')}\n"
                f"🎥 वीडियो जनरेशन प्रॉम्प्ट (Video Prompt): {scene.get('video_prompt')}\n"
            )
            
        body += "\n\n📎 तैयार वीडियो फाइल इस ईमेल के साथ अटैच है!"
        msg.attach(MIMEText(body, 'plain'))

        filename = "Ready_Anime_Short.mp4"
        if os.path.exists(filename):
            with open(filename, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {filename}")
            msg.attach(part)
            
        print("📧 जीमेल पर वीडियो और वीडियो प्रॉम्प्ट्स भेजे जा रहे हैं...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, sender_email, msg.as_string())
        server.quit()
        print("✅ वीडियो और वीडियो प्रॉम्प्ट्स सफलतापूर्वक आपके जीमेल पर भेज दिए गए हैं!")
    except Exception as e:
        print(f"❌ ईमेल भेजने में एरर आया: {e}")

async def main():
    print("🚀 बॉट शुरू हो रहा है...")
    live_trends = get_live_anime_trends()
    script = generate_script_with_gemini(live_trends)
    print(f"📌 चयनित वीडियो टाइटल: {script.get('title')}")
    await build_video(script)
    send_email_notification(script)
    print("🎉 सारी प्रक्रिया सफलतापूर्वक पूरी हुई!")

if __name__ == "__main__":
    asyncio.run(main())
