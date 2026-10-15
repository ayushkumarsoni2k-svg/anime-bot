from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import os, json, random, asyncio, requests, urllib.parse, xml.etree.ElementTree as ET
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

def get_unlimited_script():
    import requests
    import random
    
    trending_topic = "Top Airing Anime"
    scenes = []
    
    # Jikan API से असली लाइव ट्रेंडिंग एनिमी खोजने की सुरक्षित कोशिश
    for attempt in range(3):
        try:
            jikan_url = "https://api.jikan.moe/v4/top/anime?filter=airing&limit=10"
            response = requests.get(jikan_url, timeout=10)
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
                    print(f"✅ Jikan API से लाइव ट्रेंड मिल गया: {anime_title}")
                    break
        except Exception as e:
            print(f"Jikan API attempt {attempt+1} failed: {e}")
            
    # अगर जेकन एपीआई से डेटा न मिले, तो डिफ़ॉल्ट एनिमी सीन्स ले लेगा ताकि बॉट रुके नहीं
    if not scenes:
        scenes = [
            {"narration": "आज के सबसे बेहतरीन और लोकप्रिय एनिमी मोमेंट में आपका स्वागत है।", "image_prompt": "epic anime masterpiece wallpaper, cinematic"},
            {"narration": "इस दृश्य ने सभी फैंस के दिलों पर राज कर लिया है!", "image_prompt": "dramatic anime battle action, vibrant"},
            {"narration": "ऐसी ही और दिलचस्प एनिमी अपडेट्स के लिए जुड़े रहें।", "image_prompt": "cool anime hero posing, futuristic background"}
        ]
        
    return {"title": trending_topic, "scenes": scenes}

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
    import random
    from PIL import Image
    
    clips = []
    scenes = script.get("scenes", [])
    
    if not scenes:
        title = script.get("title", "Epic Anime Moment")
        scenes = [
            {"narration": f"साल 2026 में एनीमी की दुनिया में भूचाल आ गया है!", "image_prompt": f"masterpiece 8k anime key visual, solo leveling, epic scene"},
            {"narration": f"हर कोई इस जबरदस्त मोड़ को देखकर हैरान है!", "image_prompt": f"dramatic anime battle action, vibrant colors, cinematic"},
            {"narration": f"क्या होने वाला है आगे? आइए जानते हैं इस शानदार सफर में।", "image_prompt": f"mysterious anime hero looking at horizon, beautiful sunset"}
        ]
    
    for i, scene in enumerate(scenes):
        narration_text = scene.get("narration", script.get("title", "Anime Trend"))
        img_prompt = scene.get("image_prompt", "masterpiece anime style, high quality")
        
        aud_file = f"scene_{i}.mp3"
        img_file = f"scene_{i}.jpg"
        
        # 1. डीप वॉइस जनरेट करना
        await make_deep_voice(narration_text, aud_file)
        audio_clip = AudioFileClip(aud_file)
        
        # 2. Pollinations AI से एनिमी इमेज डाउनलोड करने की पक्की कोशिश
        encoded_prompt = urllib.parse.quote(img_prompt + ", high quality anime wallpaper, 4k")
        seed_num = random.randint(1000, 99999)
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&seed={seed_num}&nologo=true"
        
        image_downloaded = False
        for attempt in range(3):  # 3 बार कोशिश करेगा ताकि डाउनलोड फेल न हो
            try:
                res = requests.get(img_url, timeout=30)
                if res.status_code == 200 and len(res.content) > 2000:
                    with open(img_file, "wb") as f:
                        f.write(res.content)
                    # जाँच करें कि फाइल सही इमेज है या नहीं
                    with Image.open(img_file) as img_check:
                        img_check.verify()
                    image_downloaded = True
                    break
            except Exception as e:
                print(f"Attempt {attempt+1} failed for scene {i}: {e}")
                
        # अगर तीनों बार में डाउनलोड न हो, तो दूसरा एनिमी बैकअप लिंक ट्राई करेगा (सादा पेज बिल्कुल नहीं आएगा)
        if not image_downloaded:
            backup_url = f"https://image.pollinations.ai/prompt/epic%20anime%20fighting%20scene%20wallpaper?width=720&height=1280&seed={seed_num}"
            res = requests.get(backup_url, timeout=30)
            with open(img_file, "wb") as f:
                f.write(res.content)
                
        dur = audio_clip.duration + 0.3
        base_img = Image.open(img_file).convert("RGB")
        base_img = base_img.resize((720, 1280))
        base_img.save(img_file)
        
        img_clip = ImageClip(img_file).set_duration(dur)
        zoom_clip = img_clip.resize(lambda t: 1 + 0.03 * (t / dur))
        video_scene = zoom_clip.set_audio(audio_clip)
        clips.append(video_scene)
        
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile("Ready_Anime_Short.mp4", fps=24, codec="libx264", audio_codec="aac")
    
    with open("Video_Title.txt", "w", encoding="utf-8") as f:
        f.write(script.get("title", "Trending Anime Short"))
        
    print("✅ शानदार एनिमी वीडियो सफलतापूर्वक बन गया!")



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
