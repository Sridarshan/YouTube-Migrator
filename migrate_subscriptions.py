import os
import csv
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes required for YouTube Data API
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
LOG_FILE = 'processed_subscriptions.log'

def get_authenticated_service(client_secrets_file, token_file, account_label):
    creds = None
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print(f"\nAuthenticating {account_label}...")
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('youtube', 'v3', credentials=creds)

def subscribe_to_channel(youtube, channel_id):
    request = youtube.subscriptions().insert(
        part="snippet",
        body={
            "snippet": {
                "resourceId": {
                    "kind": "youtube#channel",
                    "channelId": channel_id
                }
            }
        }
    )
    return request.execute()

def load_processed_channels():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def log_processed_channel(channel_id):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{channel_id}\n")

def main():
    client_secrets = 'client_secrets.json'
    csv_file = 'subscriptions.csv'

    if not os.path.exists(client_secrets):
        print(f"Error: {client_secrets} not found.")
        return

    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found.")
        return

    dest_youtube = get_authenticated_service(client_secrets, 'dest_token.pickle', "Destination Account")
    processed_channels = load_processed_channels()

    subscriptions_to_add = []
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Channel Id'] not in processed_channels:
                subscriptions_to_add.append({
                    'id': row['Channel Id'],
                    'title': row['Channel Title']
                })

    if not subscriptions_to_add:
        print("All channels from CSV are already processed or the CSV is empty.")
        return

    print(f"Found {len(subscriptions_to_add)} new channels to subscribe to. ({len(processed_channels)} already processed)")

    for i, sub in enumerate(subscriptions_to_add):
        channel_id = sub['id']
        channel_title = sub['title']
        print(f"[{i+1}/{len(subscriptions_to_add)}] Subscribing to: {channel_title}")
        
        try:
            subscribe_to_channel(dest_youtube, channel_id)
            log_processed_channel(channel_id)
            print(f"  Successfully subscribed.")
        except Exception as e:
            if "subscriptionDuplicate" in str(e):
                print(f"  Already subscribed (detected by API).")
                log_processed_channel(channel_id)
            elif "quotaExceeded" in str(e):
                print(f"\nCRITICAL: Quota exceeded. Stopping for today.")
                print(f"Successfully processed {i} channels in this run.")
                print("Please wait until tomorrow (Midnight PT) to resume.")
                break
            else:
                print(f"  Failed: {e}")

    print("\nProcess finished for this session.")

if __name__ == '__main__':
    main()
