import os
import json
import random
import asyncio
import requests
import urllib.parse
import edge_tts
from PIL import Image
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# PIL Antialias Fix for MoviePy compatibility
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

def get_live_anime_trends():
    """Step 1: Fetch live trending anime from Jikan API with fallback"""
    anime_data_list = []
    for attempt in range(3):
        try:
            url = "https://api.jikan.moe/v4/top/anime?filter=airing&limit=15"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                for item in items:
                    title = item.get("title", "Anime")
                    synopsis = item.get("synopsis", "An epic journey.")[:150]
                    anime_data_list.append(f"Anime: {title} | Details: {synopsis}")
                if anime_data_list:
                    print("✅ Jikan API से लाइव ट्रेंड्स मिल गए!")
                    break
        except Exception as e:
            print(f"Jikan API attempt {attempt+1} failed: {e}")
            
    if not anime_data_list:
        print("⚠️ Jikan API कनेक्ट नहीं हुआ, डिफ़ॉल्ट ट्रेंड्स का उपयोग हो रहा है।")
        anime_data_list = [
            "Anime: Solo Leveling | Details: Hunters and monsters in a dark fantasy world.",
            "Anime: Demon Slayer | Details: Tanjiro's epic battle against demons.",
            "Anime: Jujutsu Kaisen | Details: Sorcerers fighting cursed spirits in modern Tokyo."
        ]
        
    return "\n".join(anime_data_list)

def generate_script_with_gemini(live_trends):
    """Step 2: Send live trends to Gemini API to get a 4-scene Hindi/Hinglish script in JSON"""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("❌ GEMINI_API_KEY GitHub Secrets में नहीं मिली!")
        
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
You are a viral Hindi/Hinglish Anime YouTube Shorts creator. 
Here are the current live trending anime topics:
{live_trends}

Pick ONE super interesting anime topic from above and write a strict 4-scene dramatic Hindi/Hinglish script.
Return ONLY valid JSON format matching this exact structure, with no extra text or markdown blocks:
{{
  "title": "Catchy Anime Title ⚡ #shorts #anime",
  "scenes": [
    {{
      "narration": "पहली गहरी और दमदार हिंदी नरेटर लाइन (12-15 शब्द).",
      "image_prompt": "masterpiece 8k anime key visual, dramatic epic scene, cinematic lighting"
    }},
    {{
      "narration": "दूसरी रोमांचक हिंदी नरेटर लाइन (12-15 शब्द).",
      "image_prompt": "dramatic anime battle action, vibrant colors, highly detailed"
    }},
    {{
      "narration": "तीसरी सस्पेंस वाली हिंदी नरेटर लाइन (12-15 शब्द).",
      "image_prompt": "mysterious dark anime character standing, moody atmosphere"
    }},
    {{
      "narration": "चौथी और आखिरी निष्कर्ष वाली हिंदी नरेटर लाइन (12-15 शब्द).",
      "image_prompt": "epic anime hero looking at horizon, beautiful sunset"
    }}
  ]
}
"""
    
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
                # Clean markdown json wrappers if present
                clean_text = candidate_text.replace("```json", "").replace("```", "").strip()
                script_data = json.loads(clean_text)
                print("✅ Gemini API से स्क्रिप्ट सफलतापूर्वक बन गई!")
                return script_data
        except Exception as e:
            print(f"Gemini API attempt {attempt+1} failed: {e}")
            
    # Fallback script if Gemini fails
    return {
        "title": "Epic Anime Moment 🔥 #shorts",
        "scenes": [
            {"narration": "साल 2026 में एनीमी की दुनिया में भूचाल आ गया है!", "image_prompt": "masterpiece 8k anime key visual"},
            {"narration": "हर कोई इस जबरदस्त और खतरनाक मोड़ को देखकर हैरान है!", "image_prompt": "dramatic anime battle action"},
            {"narration": "इस कैरेक्टर की ताकत ने पूरी दुनिया को पीछे छोड़ दिया है!", "image_prompt": "dark anime character standing with power"},
            {"narration": "क्या होने वाला है आगे? कमेंट में जरूर बताएं!", "image_prompt": "epic anime hero looking at horizon"}
        ]
    }

async def make_deep_voice(text, filename):
    """Step 3: Generate deep Hindi voiceover using Edge TTS"""
    communicate = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural", rate="+5%", pitch="-8Hz")
    await communicate.save(filename)

async def build_video(script):
    """Step 4: Download images, attach voiceovers, add zoom effect, and concatenate scenes"""
    clips = []
    scenes = script.get("scenes", [])
    
    for i, scene in enumerate(scenes):
        narration_text = scene.get("narration", "Anime Trend")
        img_prompt = scene.get("image_prompt", "anime masterpiece")
        
        aud_file = f"scene_{i}.mp3"
        img_file = f"scene_{i}.jpg"
        
        print(f"🎬 प्रोसेसिंग सीन {i+1}...")
        
        # 1. Voiceover generate karo
        await make_deep_voice(narration_text, aud_file)
        audio_clip = AudioFileClip(aud_file)
        
        # 2. Pollinations AI se image download karo with safe fallback
        image_saved = False
        try:
            encoded_prompt = urllib.parse.quote(img_prompt + ", high quality anime wallpaper")
            seed_num = random.randint(100, 99999)
            img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&seed={seed_num}&nologo=true"
            
            res = requests.get(img_url, timeout=20)
            if res.status_code == 200 and len(res.content) > 1000:
                with open(img_file, "wb") as f:
                    f.write(res.content)
                with Image.open(img_file) as test_img:
                    test_img.verify()
                image_saved = True
        except Exception as e:
            print(f"Image download error for scene {i}: {e}")
            
        # Agar image download fail ho jaye to direct backup image use karo
        if not image_saved:
            print(f"⚠️ Backup image use ki ja rahi hai scene {i} ke liye...")
            backup_url = f"https://image.pollinations.ai/prompt/dark%2520anime%2520character%2520standing%2520moody%2520lighting%2520masterpiece?width=720&height=1280&seed={seed_num}&nologo=true"
            res = requests.get(backup_url, timeout=20)
            with open(img_file, "wb") as f:
                f.write(res.content)
                
        # 3. Process image and add smooth zoom effect
        dur = audio_clip.duration + 0.3
        base_img = Image.open(img_file).convert("RGB")
        base_img = base_img.resize((720, 1280))
        base_img.save(img_file)
        
        img_clip = ImageClip(img_file).set_duration(dur)
        zoom_clip = img_clip.resize(lambda t: 1 + 0.03 * (t / dur))
        video_scene = zoom_clip.set_audio(audio_clip)
        clips.append(video_scene)
        
    # 4. Join all scenes into final video
    print("🔄 सभी सीन्स को जोड़ा जा रहा है...")
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile("Ready_Anime_Short.mp4", fps=24, codec="libx264", audio_codec="aac")
    
    with open("Video_Title.txt", "w", encoding="utf-8") as f:
        f.write(script.get("title", "Trending Anime Short"))
        
    print("✅ शानदार 4-सीन वाला एनिमी शॉर्ट वीडियो सफलतापूर्वक बन गया!")

async def main():
    print("🚀 बॉट शुरू हो रहा है...")
    live_trends = get_live_anime_trends()
    script = generate_script_with_gemini(live_trends)
    print(f"📌 चयनित वीडियो टाइटल: {script.get('title')}")
    await build_video(script)
    print("🎉 प्रक्रिया पूरी हुई!")

if __name__ == "__main__":
    asyncio.run(main())
