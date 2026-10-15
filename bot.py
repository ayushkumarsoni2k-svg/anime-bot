import os
import json
import random
import asyncio
import requests
import urllib.parse
import edge_tts
from PIL import Image
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# PIL Antialias Fix for compatibility
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

def get_unlimited_script():
    trending_topic = "Top Airing Anime"
    scenes = []
    
    # Try fetching from Jikan API safely with retries
    for attempt in range(3):
        try:
            jikan_url = "https://api.jikan.moe/v4/top/anime?filter=airing&limit=10"
            response = requests.get(jikan_url, timeout=8)
            if response.status_code == 200:
                data = response.json()
                anime_list = data.get("data", [])
                if anime_list:
                    selected_anime = random.choice(anime_list)
                    anime_title = selected_anime.get("title", "Trending Anime")
                    synopsis = selected_anime.get("synopsis", "An incredible journey begins.")[:120]
                    trending_topic = anime_title
                    
                    scenes = [
                        {"narration": f"साल 2026 में दुनिया भर में धूम मचा रहा है यह शानदार एनीमी, जिसका नाम है {anime_title}!", "image_prompt": f"masterpiece 8k anime key visual of {anime_title}, epic scene"},
                        {"narration": f"इसकी कहानी और प्लॉट के बारे में जानकर आप हैरान रह जाएंगे: {synopsis}...", "image_prompt": f"dramatic anime action scene, vibrant colors, cinematic lighting"},
                        {"narration": f"क्या आपने इस बेहतरीन एनीमी को देखा है? हमें कमेंट में जरूर बताएं!", "image_prompt": f"epic anime hero looking at the sky, beautiful sunset, highly detailed"}
                    ]
                    print(f"✅ Live trend fetched: {anime_title}")
                    break
        except Exception as e:
            print(f"Jikan attempt {attempt+1} failed: {e}")
            
    # Absolute safe fallback if network/API is blocked
    if not scenes:
        print("⚠️ Using robust fallback anime scenes.")
        scenes = [
            {"narration": "आज के सबसे बेहतरीन और लोकप्रिय एनिमी मोमेंट में आपका स्वागत है।", "image_prompt": "epic anime masterpiece wallpaper, cinematic"},
            {"narration": "इस दृश्य ने सभी फैंस के दिलों पर राज कर लिया है!", "image_prompt": "dramatic anime battle action, vibrant"},
            {"narration": "ऐसी ही और दिलचस्प एनिमी अपडेट्स के लिए जुड़े रहें।", "image_prompt": "cool anime hero posing, futuristic background"}
        ]
        
    return {"title": trending_topic, "scenes": scenes}

async def make_deep_voice(text, filename):
    communicate = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural", rate="+5%", pitch="-8Hz")
    await communicate.save(filename)

async def build_video(script):
    clips = []
    scenes = script.get("scenes", [])
    
    for i, scene in enumerate(scenes):
        narration_text = scene.get("narration", "Anime Trend")
        img_prompt = scene.get("image_prompt", "anime masterpiece")
        
        aud_file = f"scene_{i}.mp3"
        img_file = f"scene_{i}.jpg"
        
        # 1. Generate Voiceover
        await make_deep_voice(narration_text, aud_file)
        audio_clip = AudioFileClip(aud_file)
        
        # 2. Download Image with Fallback and Validation
        encoded_prompt = urllib.parse.quote(img_prompt + ", high quality anime wallpaper")
        seed_num = random.randint(100, 99999)
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&seed={seed_num}&nologo=true"
        
        image_saved = False
        for attempt in range(3):
            try:
                res = requests.get(img_url, timeout=20)
                if res.status_code == 200 and len(res.content) > 1000:
                    with open(img_file, "wb") as f:
                        f.write(res.content)
                    with Image.open(img_file) as test_img:
                        test_img.verify()
                    image_saved = True
                    break
            except Exception as e:
                print(f"Image download attempt {attempt+1} failed for scene {i}: {e}")
                
        if not image_saved:
            print(f"Using direct backup image for scene {i}")
            backup_url = f"https://image.pollinations.ai/prompt/epic%20anime%20wallpaper?width=720&height=1280&seed={seed_num}"
            res = requests.get(backup_url, timeout=20)
            with open(img_file, "wb") as f:
                f.write(res.content)
                
        # 3. Process Video Clip with Zoom Effect
        dur = audio_clip.duration + 0.3
        base_img = Image.open(img_file).convert("RGB")
        base_img = base_img.resize((720, 1280))
        base_img.save(img_file)
        
        img_clip = ImageClip(img_file).set_duration(dur)
        zoom_clip = img_clip.resize(lambda t: 1 + 0.03 * (t / dur))
        video_scene = zoom_clip.set_audio(audio_clip)
        clips.append(video_scene)
        
    # 4. Concatenate and Export Final Video
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile("Ready_Anime_Short.mp4", fps=24, codec="libx264", audio_codec="aac")
    
    with open("Video_Title.txt", "w", encoding="utf-8") as f:
        f.write(script.get("title", "Trending Anime Short"))
        
    print("✅ शानदार एनिमी वीडियो सफलतापूर्वक बन गया!")

async def main():
    script = get_unlimited_script()
    await build_video(script)
    print("✅ प्रक्रिया पूरी हुई! Title:", script["title"])

if __name__ == "__main__":
    asyncio.run(main())
