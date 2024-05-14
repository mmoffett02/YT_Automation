import requests
import schedule
import time
import os
from google.cloud import secretmanager

def access_secret_version(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

def get_trending_videos():
    project_id = 'youtube-automation-423207'  # Replace with your actual project ID
    secret_id = 'YOUTUBE_API_KEY'  # Replace with your actual secret ID
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
    if len(videos) > 20:  # Safety check to limit the number of videos processed
        videos = videos[:20]
    return videos

def job():
    print("Executing job...")
    trending_videos = get_trending_videos()
    print(f"Number of videos fetched: {len(trending_videos)}")
    print(trending_videos)

# Schedules automation for script to run daily at midnight
schedule.every().day.at("00:00").do(job) 



while True:  # This loop will keep the application running to execute scheduled tasks
    schedule.run_pending()
    time.sleep(1)
