import json
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_SECRETS_FILE")
YOUTUBE_TOKEN_FILE = os.getenv("YOUTUBE_TOKEN_FILE")
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

credentials = None
if os.path.exists(YOUTUBE_TOKEN_FILE):
    credentials = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_FILE, SCOPES)

if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(google.auth.transport.requests.Request())
    else:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_local_server(port=0)
    
    with open(YOUTUBE_TOKEN_FILE, "w") as token:
        token.write(credentials.to_json())

youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)


def get_playlist(player):
    request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
    response = request.execute()
    for playlist in response["items"]:
        if playlist["snippet"]["title"] == player:
            return playlist["id"]

    return None


def upload_video(video_path, player, title):
    with open("video_settings.json", "r") as f:
        video_settings = json.load(f)

    settings = video_settings[player]

    print(f"Uploading video {title} from {video_path}")

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": "20",
                "description": settings["description"],
                "title": title,
                "tags": settings["tags"].split(","),
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
                "videoLanguage": "en"
            },
            "status": {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": False
            },
        },
        media_body=video_path,
    )
    response = request.execute()

    print(f"Uploaded video {response['id']}")

    video_id = response["id"]
    playlist_id = get_playlist(player)

    playlist_item_request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    )
    playlist_item_response = playlist_item_request.execute()

    print(f"Added video {video_id} to playlist {player}")


if __name__ == "__main__":
    upload_video("./edits/test.mp4", "Zen", "Test Video")