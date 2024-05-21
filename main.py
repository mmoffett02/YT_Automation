import requests
import schedule
import time
import os
import random
import json
import tempfile
import moviepy.config as mp_config
from google.cloud import secretmanager
from pytube import YouTube
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.video.fx.all import resize



# Configure MoviePy to use ImageMagick
mp_config.change_settings({"IMAGEMAGICK_BINARY": r"C:\Users\lilmi\Documents\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})




# Path to store timestamps of extracted clips
TIMESTAMPS_FILE = "extracted_timestamps.json"
TOKEN_FILE = "token.json"
CLIENT_SECRETS_FILE = "client_secret_1080854592336-c3h20km51a6760g7ngc434ut7p616has.apps.googleusercontent.com.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']




# Secret manager configurations
def access_secret_version(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")




# Get credentials and create an API client
def get_authenticated_service():
    credentials = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token:
            credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=8080)
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())
    return build('youtube', 'v3', credentials=credentials)




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

    # Check if the video is vertical
    if clip.w < clip.h:
        clip = resize(clip, height=1920)
    else:
        # Convert to vertical format if necessary
        clip = clip.resize(width=1080).fx(vfx.crop, width=1080, height=1920, x_center=clip.w / 2, y_center=clip.h / 2)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_path = os.path.join(output_folder, f"edited_clip_{int(time.time())}.mp4")
    clip.write_videofile(output_path, codec='libx264')
    print(f"Saved edited video: {output_path}")
    upload_to_youtube(output_path)




# Upload video to YouTube
def upload_to_youtube(video_file, original_title):
    youtube = get_authenticated_service()

    request_body = {
        'snippet': {
            'title': f"{original_title[:50]} | Podcast Clip",  # Truncate and add a descriptive suffix
            'description': 'Check out this amazing podcast clip! #podcast #shorts #trending',
            'tags': ['podcast', 'shorts', 'trending'],
            'categoryId': '22'  # Category ID for People & Blogs
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }

    media_file = MediaFileUpload(video_file)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )

    try:
        response = request.execute()
        print(f"Video uploaded to YouTube: {response['id']}")
    except googleapiclient.errors.HttpError as e:
        error = json.loads(e.content.decode())
        print(f"An error occurred: {error['error']['message']}")




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
            process_and_save_video(video_path, video['snippet']['title'])





# Schedules automation for script to run daily at midnight
schedule.every().day.at("00:00").do(job)




# Schedules automation for script to run every minute (used for testing purposes)
schedule.every(1).minutes.do(job)




# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
