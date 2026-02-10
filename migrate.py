import os
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes required for YouTube Data API
# https://www.googleapis.com/auth/youtube.force-ssl allows full access
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def get_authenticated_service(client_secrets_file, token_file, account_label):
    creds = None
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print(f"\nAuthenticating {account_label}...")
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('youtube', 'v3', credentials=creds)

def list_playlists(youtube):
    playlists = []
    request = youtube.playlists().list(
        part="snippet,contentDetails",
        mine=True,
        maxResults=50
    )
    while request:
        response = request.execute()
        playlists.extend(response.get('items', []))
        request = youtube.playlists().list_next(request, response)
    return playlists

def get_playlist_items(youtube, playlist_id):
    items = []
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    while request:
        response = request.execute()
        items.extend(response.get('items', []))
        request = youtube.playlistItems().list_next(request, response)
    return items

def create_playlist(youtube, title, description=""):
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
          "snippet": {
            "title": title,
            "description": description
          },
          "status": {
            "privacyStatus": "private"
          }
        }
    )
    response = request.execute()
    return response['id']

def add_video_to_playlist(youtube, playlist_id, video_id):
    request = youtube.playlistItems().insert(
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
    return request.execute()

def main():
    client_secrets = 'client_secrets.json'
    if not os.path.exists(client_secrets):
        print(f"Error: {client_secrets} not found.")
        print("Please follow these steps to get your client_secrets.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project.")
        print("3. Enable 'YouTube Data API v3' for the project.")
        print("4. Go to 'Credentials' -> 'Create Credentials' -> 'OAuth client ID'.")
        print("5. Select 'Desktop app' as Application type.")
        print("6. Download the JSON file and rename it to 'client_secrets.json' in this directory.")
        return

    # Authenticate Source Account
    source_youtube = get_authenticated_service(client_secrets, 'source_token.pickle', "Source Account")
    
    # Authenticate Destination Account
    dest_youtube = get_authenticated_service(client_secrets, 'dest_token.pickle', "Destination Account")

    print("\nFetching playlists from source account...")
    playlists = list_playlists(source_youtube)

    if not playlists:
        print("No playlists found in source account.")
        return

    print("\nAvailable Playlists:")
    for i, pl in enumerate(playlists):
        print(f"{i+1}. {pl['snippet']['title']} ({pl['contentDetails']['itemCount']} videos)")

    choice = input("\nEnter the numbers of the playlists you want to migrate (comma separated), or 'all': ")
    
    if choice.lower() == 'all':
        selected_indices = range(len(playlists))
    else:
        try:
            selected_indices = [int(x.strip()) - 1 for x in choice.split(',')]
        except ValueError:
            print("Invalid input.")
            return

    for idx in selected_indices:
        if idx < 0 or idx >= len(playlists):
            print(f"Skipping invalid index {idx+1}")
            continue
        
        pl = playlists[idx]
        title = pl['snippet']['title']
        description = pl['snippet'].get('description', '')
        print(f"\nMigrating playlist: {title}")

        # Create new playlist in destination
        new_playlist_id = create_playlist(dest_youtube, f"{title} (Migrated)", description)
        print(f"Created new playlist: {new_playlist_id}")

        # Get videos from source playlist
        videos = get_playlist_items(source_youtube, pl['id'])
        print(f"Found {len(videos)} videos. Adding to new playlist...")

        for v in videos:
            video_id = v['contentDetails']['videoId']
            video_title = v['snippet']['title']
            try:
                add_video_to_playlist(dest_youtube, new_playlist_id, video_id)
                print(f"  Added: {video_title}")
            except Exception as e:
                print(f"  Failed to add {video_title}: {e}")

    print("\nMigration complete!")

if __name__ == '__main__':
    main()
