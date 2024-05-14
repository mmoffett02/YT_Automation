# YouTube Automation

This project automates the process of fetching trending YouTube videos and integrates Google Cloud Secret Manager for securely managing the API key.

## Features
- Fetches trending YouTube videos.
- Schedules automation to run daily at midnight.
- Downloads the videos to a specified folder
- Uses Google Cloud Secret Manager to manage API keys securely.

## Setup
1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/YT_Automation.git
    cd YT_Automation
    ```

2. **Set up a Python virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up Google Cloud Secret Manager**:
    - Follow the steps to create a secret for the YouTube API key.
    - Download the JSON key file and set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable:
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-file.json"
    ```

## Usage
Run the script:
```bash
python main.py
