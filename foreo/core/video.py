from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
from gtts import gTTS
from transformers import AutoTokenizer, LongT5ForConditionalGeneration
import torch
import os
import random
import requests
from typing import List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def summarize_for_video(summaries: list) -> str:
    """Summarize content to fit 60 second video"""
    combined = " ".join(summaries)
    tokenizer = AutoTokenizer.from_pretrained("google/long-t5-tglobal-base")
    model = LongT5ForConditionalGeneration.from_pretrained("google/long-t5-tglobal-base")

    if torch.cuda.is_available():
        model = model.to('cuda')

    prompt = f"Summarize this into a 50-second script:\n{combined}"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

    if torch.cuda.is_available():
        inputs = {key: value.to('cuda') for key, value in inputs.items()}

    summary_ids = model.generate(inputs['input_ids'],
                               max_length=150,  # ~60 seconds when spoken
                               min_length=100,
                               num_beams=4)

    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def create_video(summaries: List[str],
                background_folder: str = "backgrounds",
                output_path: str = "output.mp4",
                ) -> None:
    """
    Creates a 60-second video with TTS narration, subtitles, and background footage.

    Args:
        summaries: List of summarized text segments
        background_folder: Folder containing background videos/images
        output_path: Output video file path
        duration: Target duration in seconds (default: 60)
    """
    # Get 60-second summary
    video_script = summarize_for_video(summaries)
    tts = gTTS(text=video_script, lang='en')
    tts.save("temp_audio.mp3")
    audio = AudioFileClip("temp_audio.mp3")

    # Adjust audio speed if needed


    w, h = 1080, 1920  # Standard vertical video resolution
    background = ColorClip(size=(w, h), color=(255, 255, 255))
    background = background.with_duration(audio.duration)

    # Resize background to 9:16 aspect ratio (vertical video)
    target_width = int(background.h * 9/16)
    background = background.resized(width=target_width)

    # Center crop if needed
    if background.w > target_width:
        x1 = (background.w - target_width) // 2
        background = background.crop(x1=x1, y1=0,
                                  x2=x1+target_width,
                                  y2=background.h)

    # Loop or trim background to match duration
    if background.duration < audio.duration:
        background = background.loop(duration=audio.duration)
    else:
        background = background.subclipped(0, audio.duration)

    # Generate subtitles
    words = video_script.split()
    words_per_clip = 3  # Reduced for better readability
    time_per_clip = audio.duration / (len(words) / words_per_clip)

    subtitle_clips = []
    for i in range(0, len(words), words_per_clip):
        subtitle_text = " ".join(words[i:i + words_per_clip])

        font="./Arial.ttf"
        subtitle = TextClip(text = subtitle_text,
                    font=font,
                    color='#ffffff',
                    stroke_color='#000000',
                    stroke_width=2,
                    size=(int(background.w * 0.9,), int(200)),
                    method='caption')


        start_time = (i/words_per_clip) * time_per_clip
        subtitle = subtitle.with_position(('center', 'bottom'))
        subtitle = subtitle.with_start(start_time)
        subtitle = subtitle.with_duration(time_per_clip)
        subtitle_clips.append(subtitle)

    # Combine everything
    final_video = CompositeVideoClip([
        background,
        *subtitle_clips
    ]).with_audio(audio)

    # Set final duration
    final_video = final_video.with_duration(audio.duration)

    # Write final video
    final_video.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        preset='medium'  # Adjust for speed/quality trade-off
    )

    # Cleanup
    os.remove("temp_audio.mp3")
    background.close()
    audio.close()
    final_video.close()
    for clip in subtitle_clips:
        clip.close()

def post_to_youtube(video_file, title, description, tags, category_id='22', privacy_status='public'):
    """
    Upload a video to YouTube.

    Parameters:
    - video_file (str): Path to the video file.
    - title (str): Title of the video.
    - description (str): Description of the video.
    - tags (list): List of tags for the video.
    - category_id (str): YouTube video category ID (default: 22 for People & Blogs).
    - privacy_status (str): Privacy setting (default: 'public').

    Returns:
    - dict: Response from the YouTube API.
    """
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    # Authenticate the user
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json', SCOPES
    )
    credentials = flow.run_local_server(port=0)
    youtube = build('youtube', 'v3', credentials=credentials)

    # Define video metadata
    request_body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }

    # Upload video
    media_file = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    response = youtube.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=media_file
    ).execute()

    print(f"Video uploaded successfully: {response['id']}")
    return response

def post_to_tiktok(video_file, access_token):
    """
    Upload a video draft to TikTok.

    Parameters:
    - video_file (str): Path to the video file on your local machine.
    - access_token (str): TikTok API access token for the authorized user.

    Returns:
    - dict: Response from TikTok API with status or errors.
    """
    # Get video size
    video_size = os.path.getsize(video_file)
    chunk_size = video_size  # Single chunk upload

    # Step 1: Initialize upload
    init_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    init_payload = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": chunk_size,
            "total_chunk_count": 1
        }
    }
    init_response = requests.post(init_url, headers=headers, json=init_payload)

    if init_response.status_code != 200:
        return {"error": f"Initialization failed: {init_response.json()}"}

    init_data = init_response.json().get("data", {})
    upload_url = init_data.get("upload_url")
    publish_id = init_data.get("publish_id")

    if not upload_url or not publish_id:
        return {"error": "Missing upload_url or publish_id in initialization response."}

    print(f"Upload initialized. Publish ID: {publish_id}")

    # Step 2: Upload video file
    with open(video_file, "rb") as video:
        video_data = video.read()
    upload_headers = {
        "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
        "Content-Type": "video/mp4"
    }
    upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)

    if upload_response.status_code != 200:
        return {"error": f"Video upload failed: {upload_response.json()}"}

    print("Video uploaded successfully.")

    # Step 3: Check upload status
    status_url = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
    status_payload = {"publish_id": publish_id}
    status_response = requests.post(status_url, headers=headers, json=status_payload)

    if status_response.status_code != 200:
        return {"error": f"Failed to fetch status: {status_response.json()}"}

    print(f"Status check completed. Response: {status_response.json()}")
    return status_response.json()