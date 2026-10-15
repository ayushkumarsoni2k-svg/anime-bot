import os, json, random, asyncio, requests, urllib.parse, xml.etree.ElementTree as ET
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

def fetch_live_trending_anime():
    live_trends = []
    rss_url = "https://news.google.com/rss/search?q=trending+anime+OR+Solo+Leveling+OR+Re+Zero+OR+Jujutsu+Kaisen&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        res = requests.get(rss_url, timeout=10)
        root = ET.fromstring(res.text)
        for item in root.findall('.//item')[:12]:
            live_trends.append(item.find('title').text)
    except Exception as e:
        print("RSS info:", e)

    try:
        jikan = requests.get("https://api.jikan.moe/v4/top/anime?filter=airing&limit=10", timeout=10).json()
        for a in jikan.get("data", []):
            live_trends.append(f"{a['title']}: {a.get('synopsis', '')[:120]}")
    except Exception as e:
        print("Jikan info:", e)

    random.shuffle(live_trends)
    return "\n".join(live_trends[:10])

def get_unlimited_script():
    api_key = os.environ["GEMINI_API_KEY"].strip()
    live_data = fetch_live_trending_anime()

    prompt = f"""You are a viral Hindi Anime YouTube Shorts creator.
Live trending anime right now:
{live_data}

Pick ONE super interesting anime topic from above and write a 5-scene dramatic Hindi script.
Return ONLY valid JSON:
{{
  "title": "Viral Hindi Anime Title 😱🔥 #shorts #anime #hindianime",
  "scenes": [
    {{
      "narration": "गहरी और दमदार हिंदी नैरेटर लाइन (12-15 words)",
      "image_prompt": "masterpiece 8k anime key visual, dark cinematic lighting, vertical 9:16, detailed action scene"
    }}
  ]
}}
Exactly 5 scenes."""

    models_res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}").json()
    valid_models = [
        m["name"] for m in models_res.get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", []) and "gemini" in m["name"]
    ]
    valid_models.reverse()

    for model_name in valid_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
        if "candidates" in res:
            raw = res["candidates"][0]["content"]["parts"][0]["text"]
            clean = raw[raw.find("{"):raw.rfind("}")+1]
            return json.loads(clean)

    raise Exception(f"API Error: {models_res}")

async def make_deep_voice(text, filename):
    communicate = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural", rate="+5%", pitch="-8Hz")
    await communicate.save(filename)

async def build_video(script):
    audio_file = "voiceover.mp3"
    await make_deep_voice(script["narration"], audio_file)
    
    audio_clip = AudioFileClip(audio_file)
    total_duration = audio_clip.duration
    
    title = script.get("title", "anime action")
    clean_prompt = f"High quality anime style, cinematic lighting, vibrant colors, epic scene representing {title}"
    
    img_file = "main_anime_image.jpg"
    
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(clean_prompt)}"
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            with open(img_file, "wb") as f:
                f.write(response.content)
        else:
            raise Exception("API Error")
    except Exception as e:
        print(f"Image generation failed: {e}. Using fallback image.")
        fallback_url = "https://image.pollinations.ai/prompt/epic%20anime%20hero%20wallpaper"
        res = requests.get(fallback_url)
        with open(img_file, "wb") as f:
            f.write(res.content)
            
    base_clip = ImageClip(img_file).set_duration(total_duration)
    zoom_clip = base_clip.resize(lambda t: 1 + 0.05 * (t / total_duration))
    final_video = zoom_clip.set_audio(audio_clip)
    final_video.write_videofile("Ready_Anime_Short.mp4", fps=24, codec="libx264", audio_codec="aac")
    
    with open("Video_Title.txt", "w", encoding="utf-8") as f:
        f.write(title)
    
    print("✅ वीडियो सफलतापूर्वक बन गया!")

async def main():
    script = get_unlimited_script()
    await build_video(script)
    print("✅ वीडियो सफलतापूर्वक बन गया! Title:", script["title"])
    import os
    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg["Subject"] = f"New Anime Short: {script['title']}"
    msg["From"] = os.environ["MY_GMAIL"]
    msg["To"] = os.environ["MY_GMAIL"]
    msg.set_content("यहाँ तुम्हारा नया एनिमी शॉर्ट वीडियो अटैच है। इसे डाउनलोड करके अपलोड कर लो!")

    with open("Ready_Anime_Short.mp4", "rb") as f:
        file_data = f.read()
        file_name = "Ready_Anime_Short.mp4"

    msg.add_attachment(file_data, maintype="video", subtype="mp4", filename=file_name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.environ["MY_GMAIL"], os.environ["GMAIL_APP_PASS"])
        smtp.send_message(msg)

    print("Email sent successfully with the video!")

if __name__ == "__main__":
    asyncio.run(main())
