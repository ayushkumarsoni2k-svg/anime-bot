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
    clips = []
    for i, scene in enumerate(script["scenes"]):
        img_file = f"scene_{i}.jpg"
        aud_file = f"scene_{i}.mp3"

        from PIL import Image
        from io import BytesIO
        encoded = urllib.parse.quote(scene["image_prompt"])
        img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&nologo=true&seed={random.randint(1,99999)}"
        img_saved = False
        for attempt in range(3):
            try:
                res = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
                if res.status_code == 200 and len(res.content) > 1000:
                    Image.open(BytesIO(res.content)).convert("RGB").save(img_file, "JPEG")
                    img_saved = True
                    break
            except Exception as e:
                print(f"Image error: {e}")
        if not img_saved:
            Image.new('RGB', (720, 1280), color=(15, 15, 25)).save(img_file, "JPEG")


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

if __name__ == "__main__":
    asyncio.run(main())
