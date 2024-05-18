import requests
import schedule
import time
import os
import random
import tempfile
import moviepy.config as mp_config
from google.cloud import secretmanager
from pytube import YouTube
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import json

# Configure MoviePy to use ImageMagick
mp_config.change_settings({"IMAGEMAGICK_BINARY": r"C:\Users\lilmi\Documents\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

# Path to store timestamps of extracted clips
TIMESTAMPS_FILE = "extracted_timestamps.json"

# Secret manager configurations
def access_secret_version(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# Get trending podcast videos information
def get_trending_podcast_videos():
    project_id = 'youtube-automation-423207'
    secret_id = 'YOUTUBE_API_KEY'
    api_key = access_secret_version(project_id, secret_id)
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': 'podcast',
        'type': 'video',
        'order': 'viewCount',
        'maxResults': 20,
        'key': api_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    videos = data.get('items', [])
    if len(videos) > 20:
        videos = videos[:20]
    return videos

# Video download functionality
def download_video(video_url, output_path="C:/Users/lilmi/Documents/YouTubeDownloads"):
    print(f"Starting download for: {video_url}")
    try:
        yt = YouTube(video_url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        file_path = stream.download(output_path=output_path)
        print(f"Downloaded: {yt.title}")
        return file_path
    except Exception as e:
        print(f"Failed to download video: {video_url}. Error: {str(e)}")
        return None

# Load extracted timestamps
def load_timestamps():
    if os.path.exists(TIMESTAMPS_FILE):
        with open(TIMESTAMPS_FILE, 'r') as file:
            return json.load(file)
    return {}

# Save extracted timestamps
def save_timestamps(timestamps):
    with open(TIMESTAMPS_FILE, 'w') as file:
        json.dump(timestamps, file)

# Extract a random 30-second clip from the video
def extract_random_clip(video_path, clip_duration=30):
    video = VideoFileClip(video_path)
    duration = video.duration
    timestamps = load_timestamps()
    video_id = os.path.basename(video_path)
    
    if video_id not in timestamps:
        timestamps[video_id] = []
    
    available_start_times = list(set(range(0, int(duration - clip_duration))) - set(timestamps[video_id]))
    if not available_start_times:
        print(f"No more unique 30-second clips available for {video_id}")
        return None
    
    start = random.choice(available_start_times)
    end = start + clip_duration
    timestamps[video_id].append(start)
    save_timestamps(timestamps)
    
    return video.subclip(start, end)

# Process and save the edited video
def process_and_save_video(video_path, output_folder="C:/Users/lilmi/Documents/EditedVideos"):
    clip = extract_random_clip(video_path)
    if clip is None:
        return
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_path = os.path.join(output_folder, f"edited_clip_{int(time.time())}.mp4")
    clip.write_videofile(output_path, codec='libx264')
    print(f"Saved edited video: {output_path}")

# Main job function
def job():
    print("Executing job...")
    trending_videos = get_trending_podcast_videos()
    print(f"Number of videos fetched: {len(trending_videos)}")
    for video in trending_videos:
        video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
        print(f"Downloading video: {video_url}")
        video_path = download_video(video_url)
        if video_path:
            process_and_save_video(video_path)

# Schedules automation for script to run daily at midnight
schedule.every().day.at("00:00").do(job)

# Schedules automation for script to run every minute (used for testing purposes)
schedule.every(1).minutes.do(job)

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
