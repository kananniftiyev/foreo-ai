from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
from gtts import gTTS
from transformers import AutoTokenizer, LongT5ForConditionalGeneration
import torch
import os
import random
from typing import List

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

def post_videos():
  pass