import requests
import base64
import logging
import time
import re
from urllib.parse import quote, unquote  # unquote kept for possible response decoding
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from requests.exceptions import RequestException
from difflib import SequenceMatcher

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Reduce noise from httpx and urllib3 if used under the hood
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Spotify credentials (fill with your own client ID/secret)
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""

# Telegram bot token (fill with your own bot token)
TELEGRAM_BOT_TOKEN = ""


def normalize_name(name: str) -> str:
    """Normalize artist name: remove non-alphanumeric characters and lowercase."""
    return re.sub(r"\W+", "", name).lower()


# Obtain Spotify access token using Client Credentials flow
def get_spotify_token() -> str:
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers=headers,
        data={"grant_type": "client_credentials"},
    )

    if response.status_code == 200:
        logging.info("Successfully obtained Spotify token")
        return response.json()["access_token"]
    else:
        logging.error(
            "Failed to obtain Spotify token. Status: %s, Response: %s",
            response.status_code,
            response.text,
        )
        raise Exception("Failed to obtain Spotify token")


def search_spotify_artist(artist_name: str, token: str) -> str | None:
    """Search artist on Spotify by name with fuzzy matching.

    Returns artist ID or None if not found.
    """
    headers = {"Authorization": f"Bearer {token}"}

    # Use the artist name directly in the query
    params = {
        "q": artist_name,
        "type": "artist",
        "limit": 25,
    }

    response = requests.get(
        "https://api.spotify.com/v1/search", headers=headers, params=params
    )

    if response.status_code == 200:
        artists = response.json().get("artists", {}).get("items", [])
        if artists:
            # Normalize the input artist name once
            normalized_input_name = normalize_name(artist_name)

            best_match_id = None
            highest_ratio = 0

            for artist in artists:
                found_artist_name = artist["name"]
                normalized_found_name = normalize_name(found_artist_name)

                # Calculate similarity ratio
                ratio = SequenceMatcher(
                    None, normalized_input_name, normalized_found_name
                ).ratio()

                if ratio > highest_ratio:
                    highest_ratio = ratio
                    best_match_id = artist["id"]

                # Exact match after normalization → return immediately
                if normalized_found_name == normalized_input_name:
                    logging.info(
                        "Found exact Spotify artist ID for '%s': %s",
                        artist_name,
                        artist["id"],
                    )
                    return artist["id"]

            # If no exact match, return the best match if the ratio is above a threshold
            if highest_ratio > 0.8:  # threshold can be adjusted
                logging.info(
                    "Found close Spotify artist ID for '%s': %s",
                    artist_name,
                    best_match_id,
                )
                return best_match_id
            else:
                logging.info(
                    "Artist '%s' not found as an exact or close match on Spotify.",
                    artist_name,
                )
        else:
            logging.info("No artists found on Spotify for '%s'", artist_name)

    elif response.status_code == 401:
        # Token might have expired — renew and retry once recursively
        logging.warning("Spotify token expired, requesting a new token...")
        token = get_spotify_token()
        return search_spotify_artist(artist_name, token)

    else:
        logging.error(
            "Failed to search for artist '%s' on Spotify. Status Code: %s, Response: %s",
            artist_name,
            response.status_code,
            response.text,
        )

    return None


# Search for artist on Apple Music using iTunes Search API
def search_apple_music_artist(artist_name: str, retries: int = 3) -> str | None:
    formatted_artist_name_apple = requests.utils.quote(artist_name)
    search_url = (
        f"https://itunes.apple.com/search?term={formatted_artist_name_apple}"
        f"&entity=musicArtist&limit=25"
    )

    for attempt in range(retries):
        try:
            logging.debug("Apple Music search URL: %s", search_url)
            response = requests.get(search_url)

            if response.status_code != 200:
                logging.error(
                    "Attempt %d: Failed to search for artist '%s' on Apple Music. "
                    "Status Code: %s. Response: %s",
                    attempt + 1,
                    artist_name,
                    response.status_code,
                    response.text,
                )
                time.sleep(2)
                continue

            results = response.json().get("results", [])

            if results:
                # First, try exact case-sensitive match
                for result in results:
                    found_artist_name = result["artistName"]
                    if found_artist_name.strip() == artist_name.strip():
                        artist_id = str(result["artistId"])
                        logging.info(
                            "Found exact Apple Music artist ID for '%s' (case-sensitive): %s",
                            artist_name,
                            artist_id,
                        )
                        return artist_id

                # Then, try case-insensitive match
                for result in results:
                    found_artist_name = result["artistName"]
                    if (
                        found_artist_name.strip().lower()
                        == artist_name.strip().lower()
                    ):
                        artist_id = str(result["artistId"])
                        logging.info(
                            "Found exact Apple Music artist ID for '%s' (case-insensitive): %s",
                            artist_name,
                            artist_id,
                        )
                        return artist_id

                # If still not found, proceed with normalization and fuzzy matching
                normalized_input_name = normalize_name(artist_name)
                best_match_id = None
                highest_ratio = 0

                for result in results:
                    found_artist_name = result["artistName"]
                    normalized_found_name = normalize_name(found_artist_name)
                    ratio = SequenceMatcher(
                        None, normalized_input_name, normalized_found_name
                    ).ratio()
                    logging.debug(
                        "Similarity ratio between '%s' and '%s': %s",
                        artist_name,
                        found_artist_name,
                        ratio,
                    )

                    if ratio > highest_ratio:
                        highest_ratio = ratio
                        best_match_id = str(result["artistId"])

                if highest_ratio > 0.9:  # stricter threshold for Apple Music
                    logging.info(
                        "Found close Apple Music artist ID for '%s': %s",
                        artist_name,
                        best_match_id,
                    )
                    return best_match_id
                else:
                    logging.info(
                        "Artist '%s' not found as an exact or close match on Apple Music.",
                        artist_name,
                    )
                    return None
            else:
                logging.info("Artist '%s' not found on Apple Music", artist_name)
                return None

        except RequestException as e:
            logging.error(
                "Attempt %d: RequestException while searching for artist '%s': %s",
                attempt + 1,
                artist_name,
                e,
            )
            time.sleep(2)
        except ValueError as e:
            logging.error(
                "Attempt %d: Failed to parse JSON response for artist '%s': %s",
                attempt + 1,
                artist_name,
                e,
            )
            logging.error("Response Content: %s", response.text)
            time.sleep(2)

    logging.error("All attempts failed for artist '%s' on Apple Music", artist_name)
    return None


# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hello! Send me the name of an artist and I will find their Spotify and Apple Music IDs."
    )


# Message handler for artist name
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    artist_name = update.message.text
    logging.info("Received request for artist: %s", artist_name)

    spotify_token = get_spotify_token()

    # Spotify
    spotify_artist_id = search_spotify_artist(artist_name, spotify_token)

    # Apple Music
    apple_music_artist_id = search_apple_music_artist(artist_name)

    response_message = ""

    if spotify_artist_id:
        spotify_link = f"https://open.spotify.com/artist/{spotify_artist_id}"
        response_message += f"spotify:artist:{spotify_artist_id}\n{spotify_link}\n"
    else:
        response_message += "Artist not found on Spotify\n"

    # Add an empty line between responses
    response_message += "\n"

    if apple_music_artist_id:
        apple_music_link = f"https://music.apple.com/artist/{apple_music_artist_id}"
        response_message += f"{apple_music_artist_id}\n{apple_music_link}\n"
    else:
        response_message += "Artist not found on Apple Music\n"

    logging.info("Response for artist '%s':\n%s", artist_name, response_message)

    await update.message.reply_text(response_message)


def main() -> None:
    """Bot entry point."""
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Run the bot
    application.run_polling()


if __name__ == "__main__":
    main()