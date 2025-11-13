import requests
import pandas as pd
import base64
import csv
import time

# Detect CSV delimiter automatically
def detect_delimiter(csv_file):
    with open(csv_file, "r", encoding="utf-8") as f:
        sample = f.read(1024)
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample)
        return dialect.delimiter


# Load releases data from CSV file
def load_releases(csv_file):
    delimiter = detect_delimiter(csv_file)
    releases = pd.read_csv(
        csv_file,
        delimiter=delimiter,
        dtype=str,
        quoting=csv.QUOTE_NONE,
        on_bad_lines="skip",
    )
    return releases, delimiter


# Search album on Spotify by UPC code
def search_spotify(upc, token):
    url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {token}",
    }
    params = {
        "q": f"upc:{upc}",
        "type": "album",
    }
    response = requests.get(url, headers=headers, params=params)
    # Add a 2-second pause after each request to reduce rate limiting risk
    time.sleep(2)
    if response.status_code == 200:
        data = response.json()
        if data["albums"]["items"]:
            album_id = data["albums"]["items"][0]["id"]
            album_url = f"https://open.spotify.com/album/{album_id}"
            return True, album_url
    return False, ""


# Get Spotify access token
def get_spotify_token(client_id, client_secret):
    url = "https://accounts.spotify.com/api/token"
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
    }
    response = requests.post(url, headers=headers, data=data)
    print("Response status code:", response.status_code)
    print("Response content:", response.text)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        response.raise_for_status()


# Main function to execute the process
def main(csv_file, client_id, client_secret):
    # Load releases and detect delimiter
    releases, delimiter = load_releases(csv_file)

    # Assume UPC is in the first column
    upc_column = releases.columns[0]

    # Ensure 'Spotify' and 'Spotify Link' columns exist
    if "Spotify" not in releases.columns:
        releases["Spotify"] = ""
    if "Spotify Link" not in releases.columns:
        releases["Spotify Link"] = ""

    # Replace possible NaN values with empty strings
    releases["Spotify"] = releases["Spotify"].fillna("")
    releases["Spotify Link"] = releases["Spotify Link"].fillna("")

    # Batch processing settings
    batch_size = 100  # Process 100 rows at a time
    total_batches = (len(releases) // batch_size) + 1

    for batch_num in range(total_batches):
        # Get access token for each batch
        token = get_spotify_token(client_id, client_secret)
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(releases))

        # Process current batch
        for index in range(start_idx, end_idx):
            row = releases.iloc[index]
            upc = str(row[upc_column])

            spotify_status = row["Spotify"]
            spotify_link = row["Spotify Link"]

            if spotify_status == "+" and spotify_link:
                # Skip already processed row
                continue
            elif spotify_status == "-":
                # Recheck if release appears on Spotify now
                found, album_url = search_spotify(upc, token)
                if found:
                    releases.at[index, "Spotify"] = "+"
                    releases.at[index, "Spotify Link"] = album_url
                # If not found, keep '-'
            else:
                # If status is empty, perform a normal check
                found, album_url = search_spotify(upc, token)
                if found:
                    releases.at[index, "Spotify"] = "+"
                    releases.at[index, "Spotify Link"] = album_url
                else:
                    releases.at[index, "Spotify"] = "-"

        # Save intermediate result
        releases.to_csv(
            "releases_with_spotify_status_partial.csv",
            index=False,
            sep=delimiter,
        )
        print(f"Batch {batch_num + 1}/{total_batches} processed and saved.")

    # Save final result
    releases.to_csv(
        "releases_with_spotify_status.csv",
        index=False,
        sep=delimiter,
    )
    print("File 'releases_with_spotify_status.csv' successfully created.")


# Replace these with your own values before running
client_id = ""  # Spotify Client ID
client_secret = ""  # Spotify Client Secret
csv_file = ""  # Path to input CSV file


# Entry point
if __name__ == "__main__":
    main(csv_file, client_id, client_secret)