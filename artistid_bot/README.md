

# 🎧 ArtistID Finder — Spotify & Apple Music  
Telegram-based tool for fast and accurate artist profile lookup across DSPs.

This bot automates the process of locating **Spotify Artist IDs** and **Apple Music Artist IDs** using APIs, fuzzy matching, and name normalization.  
It was originally created to speed up metadata completion for digital distribution when Spotify/Apple made Artist IDs mandatory for *all* releases.

---

## ✨ Features

- 🔍 **Spotify API (Client Credentials Flow)**
- 🍏 **Apple iTunes Search API**
- 🔤 **Fuzzy matching** using `difflib.SequenceMatcher`
- 🔠 Normalization of artist names for better accuracy
- 🔗 Returns:
  - Artist name (verified)
  - Spotify profile URL
  - Spotify Artist ID
  - Apple Music Artist URL
- ⚙️ API retry logic & error handling
- 📝 CLI and Telegram-ready logic

---

## 📂 Project Structure

```
artistid_bot/
│
├── artistid.py         # Main script for Spotify/Apple artist lookup
├── spotify_check.py    # Batch checker for UPC presence on Spotify
└── README.md           # This file
```

---

## 🚀 Usage

### 🔹 1. Install dependencies
```bash
pip install requests python-dotenv
```

*(Add other dependencies if you expand the bot functionality.)*

---

### 🔹 2. Set API keys  
Create a `.env` file in the folder:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

Apple API doesn’t require authentication for basic search.

---

### 🔹 3. Run the script

#### Lookup by artist name:
```bash
python3 artistid.py "Oliver Koletzki"
```

#### Check presence of releases by UPC on Spotify:
```bash
python3 spotify_check.py upc_list.csv
```

---

## 🎯 Example Output

```
Artist: Stephan Bodzin
Spotify URL: https://open.spotify.com/artist/xxxxxx
Spotify ID: xxxxxx
Apple Music URL: https://music.apple.com/artist/xxxxxx
Match Confidence: 0.92
```

---

## 🧠 How It Works

1. Takes user input (artist name).
2. Requests Spotify token (Client Credentials).
3. Queries Spotify API `/search` endpoint.
4. Queries Apple iTunes API.
5. Normalizes names:
   - lowercase  
   - remove punctuation  
   - trim spaces  
6. Fuzzy-matches both results.
7. Returns best candidate with confidence score.
8. (Optional) Logs results for batch processing.

---

## 🛠 Technologies

- **Python**
- `requests`
- `difflib` (fuzzy matching)
- Spotify Web API
- Apple iTunes Search API
- `.env` configuration

---

## 📌 Notes

- Designed for high-volume distribution workflows (thousands of artists).  
- Greatly reduces manual search time.  
- Fully compatible with Telegram bot integration (optional).

---

## 📄 License  
MIT License