import requests
import schedule
import time
import os
from google.cloud import secretmanager
from pytube import YouTube

# Secret manager configurations
def access_secret_version(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# Get trending videos information
def get_trending_videos():
    project_id = 'youtube-automation-423207'
    secret_id = 'YOUTUBE_API_KEY'
    api_key = access_secret_version(project_id, secret_id)
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'part': 'snippet,contentDetails,statistics',
        'chart': 'mostPopular',
        'regionCode': 'US',
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
        stream.download(output_path=output_path)
        print(f"Downloaded: {yt.title}")
    except Exception as e:
        print(f"Failed to download video: {video_url}. Error: {str(e)}")

# Print outputs and download videos
def job():
    print("Executing job...")
    trending_videos = get_trending_videos()
    print(f"Number of videos fetched: {len(trending_videos)}")
    for video in trending_videos:
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        print(f"Downloading video: {video_url}")
        download_video(video_url)

# Schedules automation for script to run daily at midnight
schedule.every().day.at("00:00").do(job)

# Schedules automation for script to run every minute (used for testing purposes)
#schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
