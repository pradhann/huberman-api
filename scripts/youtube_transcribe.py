import concurrent.futures
import csv
import json
import logging
import os

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

MAX_DURATION_PER_CHUNK = 60


def ensure_directory(directory: str):
    """
    Ensure that the input directory exists, and create it if it does not.

    Parameters:
        directory (str): Directory path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def transcribe_episode(episode_data: dict):
    sanitized_title = episode_data.get("sanitized_title", "Untitled")

    output_dir = "data/transcribed/youtube"
    ensure_directory(output_dir)
    output_file_path = os.path.join(output_dir, f"{sanitized_title}.csv")

    # Check if the transcription already exists
    if os.path.exists(output_file_path):
        print("Already exists")
        logging.info(
            f"Transcription for episode {sanitized_title} already exists. Skipping."
        )
        return

    youtube_url = episode_data.get("youtube_url")
    if youtube_url != None:
        transciption = get_transcript_from_youtube_url(youtube_url)
        if transciption != None:
            save_transcript(output_file_path, transciption)
    return


def get_transcript_from_youtube_url(url):
    video_id = extract_video_id_from_url(url)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    except NoTranscriptFound:
        try:
            # If 'en' is not available, try 'en-US'
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["en-US"]
            )
        except NoTranscriptFound:
            # If neither is available, return None or we can modify logic somewhere outside to use the whisper transcripts
            return None
    except TranscriptsDisabled:
        return None
    return transcript


def save_transcript(filepath, transcription):
    # Open the CSV file
    with open(filepath, "w", newline="") as csvfile:
        fieldnames = ["start", "text"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        buffered_entries = []  # Collects entries until they should be written out
        current_start = transcription[0]["start"] if transcription else 0.0

        for i, entry in enumerate(transcription):
            # If adding the current entry will exceed MAX_DURATION_PER_CHUNK seconds, or if it's the last entry
            if (
                entry["start"] - current_start > MAX_DURATION_PER_CHUNK
                or i == len(transcription) - 1
            ):
                # If it's the last entry, we append it to the buffered entries
                if i == len(transcription) - 1:
                    buffered_entries.append(entry)

                # Write out the buffered entries so far
                writer.writerow(
                    {
                        "start": current_start,
                        "text": " ".join(e["text"] for e in buffered_entries),
                    }
                )

                buffered_entries = [entry]
                current_start = entry["start"]

            else:
                buffered_entries.append(entry)

    print("CSV conversion done.")


def extract_video_id_from_url(url):
    if "youtu.be" in url:
        # Handles the case: https://youtu.be/VIDEO_ID
        return url.split("/")[-1]
    elif "youtube.com" in url:
        # Handles the standard format: https://www.youtube.com/watch?v=VIDEO_ID&...
        return url.split("v=")[1].split("&")[0]
    else:
        # Not a valid YouTube URL
        return None


def main():
    JSON_PATH = "data/HubermanPodcastEpisodes.json"
    if not os.path.exists(JSON_PATH):
        logging.error(f"The JSON file {JSON_PATH} does not exist.")
        exit(1)

    with open(JSON_PATH, "r") as f:
        episodes = json.load(f)
    print(episodes[0])

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(transcribe_episode, episodes))

    logging.info("Finished transcribing all episodes.")


if __name__ == "__main__":
    main()
