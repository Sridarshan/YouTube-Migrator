# YouTube Migration Tools

This repository contains Python scripts to help you migrate your YouTube data from one account to another using the YouTube Data API v3. 

### 🚀 Features
- **Playlist Migration**: Copies playlists from a source account to a destination account.
- **Subscription Migration**: Subscribes your new account to channels listed in a `subscriptions.csv` file.
- **Resume Support**: The subscription script tracks progress, allowing you to resume if you hit API quota limits.
- **Security**: Designed to use a single GCP project to manage multiple account authentications.

---

## 🛠 Prerequisites

1. **Python 3.x** installed.
2. **Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project.
   - Enable the **YouTube Data API v3** in the "Library" section.
3. **OAuth Credentials**:
   - Go to "Credentials" -> "Create Credentials" -> "OAuth client ID".
   - Set the application type to **Desktop app**.
   - Download the JSON file and rename it to `client_secrets.json` in this project directory.
   - **Important**: In the "OAuth consent screen" settings, add your email addresses as **Test Users**.

---

## 📦 Installation

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/Sridarshan/YouTube-Migrator.git
cd YouTube-Migrator

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 📽 1. Migrating Playlists

This script will fetch playlists from your **Source Account** and recreate them in your **Destination Account**.

1. Run the script:
   ```bash
   python3 migrate.py
   ```
2. Follow the browser prompts to log in to your **Source Account** first.
3. Follow the browser prompts to log in to your **Destination Account** second.
4. Select the playlists you wish to migrate from the list provided.

---

## 🔔 2. Migrating Subscriptions

This script reads from a `subscriptions.csv` (exported from YouTube Google Takeout) and subscribes your new account to those channels.

1. Place your `subscriptions.csv` in the root folder.
2. Run the script:
   ```bash
   python3 migrate_subscriptions.py
   ```
3. The script will log progress in `processed_subscriptions.log`. If it stops due to quota limits, run it again the next day to resume where it left off.

---

## ⚠️ Important: API Quotas

The YouTube Data API has a default daily limit of **10,000 units**.
- **Playlist Video Insertion**: 50 units per video.
- **Channel Subscription**: 50 units per channel.
- **Standard limit**: ~200 actions per day.

If you receive a `quotaExceeded` error, you must wait until **Midnight Pacific Time** for the limit to reset before continuing.

---

## 🧹 Resetting Sessions

If you want to log in with different accounts, run the reset script to clear stored tokens:
```bash
./reset_tokens.sh
```

---

## 🔒 Security Note
`client_secrets.json`, `*.pickle` files, and `.csv` files are ignored by git to protect your privacy and credentials. Never commit these files to a public repository.
