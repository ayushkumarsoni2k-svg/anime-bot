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
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    import textwrap

    clips = []
    backup_imgs = []
    try:
        jikan_res = requests.get("https://api.jikan.moe/v4/top/anime?filter=airing&limit=10", timeout=10).json()
        for item in jikan_res.get("data", []):
            img_link = item.get("images", {}).get("jpg", {}).get("large_image_url")
            if img_link:
                backup_imgs.append(img_link)
    except Exception:
        pass

    for i, scene in enumerate(script["scenes"]):
        img_file = f"scene_{i}.jpg"
        aud_file = f"scene_{i}.mp3"

        short_prompt = scene["image_prompt"][:120]
        encoded = urllib.parse.quote(short_prompt)
        seed = random.randint(1, 99999)
        
        urls_to_try = [
            f"https://pollinations.ai/p/{encoded}?width=720&height=1280&seed={seed}&nologo=true",
            f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&seed={seed}&model=flux&nologo=true"
        ]
        if backup_imgs:
            urls_to_try.append(random.choice(backup_imgs))

        base_img = None
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

        for url in urls_to_try:
            try:
                res = requests.get(url, headers=headers, timeout=25)
                if res.status_code == 200 and len(res.content) > 2000:
                    base_img = Image.open(BytesIO(res.content)).convert("RGB")
                    base_img = base_img.resize((720, 1280))
                    break
            except Exception as e:
                print(f"URL failed: {e}")

        if base_img is None:
            base_img = Image.new('RGB', (720, 1280), color=(25, 20, 45))

        draw = ImageDraw.Draw(base_img)
        narration_text = scene.get("narration", "")
        wrapped_text = "\n".join(textwrap.wrap(narration_text, width=28))

        draw.rectangle([(40, 880), (680, 1160)], fill=(0, 0, 0))
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except Exception:
            font = ImageFont.load_default()

        draw.multiline_text((60, 910), wrapped_text, fill=(255, 255, 0), font=font, spacing=8)
        base_img.save(img_file, "JPEG")

        await make_deep_voice(scene["narration"], aud_file)

        audio_clip = AudioFileClip(aud_file)
        image_clip = ImageClip(img_file).set_duration(audio_clip.duration + 0.3).set_audio(audio_clip)
        clips.append(image_clip)

    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile("Ready_Anime_Short.mp4", fps=24, codec="libx264", audio_codec="aac")
    with open("Video_Title.txt", "w", encoding="utf-8") as f:
        f.write(script["title"])


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
