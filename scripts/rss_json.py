import json
import os
import re
import logging
import feedparser
import unicodedata
import requests
from bs4 import BeautifulSoup

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[logging.StreamHandler()],
)

# Constants
RSS_URL = "https://feeds.megaphone.fm/hubermanlab"
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "HubermanPodcastEpisodes.json")
HUBERMAN_PREMIUM_LINK = "https://hubermanlab.com/premium"
HUBERMAN_TOUR_LINK = "https://hubermanlab.com/tour"
HUBERMAN_INTRO_LINK = "https://hubermanlab.com/welcome-to-the-huberman-lab-podcast"


def remove_unicode_characters(text: str) -> str:
    """
    Remove special Unicode characters from text.

    Parameters:
        text (str): The original text containing Unicode characters.

    Returns:
        str: Text with Unicode characters removed.
    """
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("utf-8", "ignore")
    )


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize the filename by removing or replacing characters that are not safe
    for a filename and trim the filename to be within the filesystem's max_length.

    Parameters:
        filename (str): The original filename to be sanitized.
        max_length (int, optional): The maximum length for the filename. Defaults to 255.

    Returns:
        str: The sanitized filename.
    """

    # Remove special characters other than hyphens and spaces
    sanitized = re.sub(r"[^\w\s-]", "", filename)
    # Replace spaces with hyphens
    sanitized = re.sub(r"\s+", "-", sanitized)
    # Trim to max_length
    return sanitized[:max_length]


def get_podcast_youtube_link(entry):
    """
    This function takes in a url for the podcast in hubermanlab webpage
    and returns the youtube URL for the podcast.

    Parameters:
        URL of podcast page in hubermanlab website: https://hubermanlab.com/dr-immordino-yang-how-emotions-and-social-factors-impact-learning/

    Returns:
        str: Youtube URL
    """
    url = entry.link

    if (
        url == HUBERMAN_PREMIUM_LINK
        or url == HUBERMAN_TOUR_LINK
        or url == HUBERMAN_INTRO_LINK
    ):
        return switch(entry.title)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # find <p> because of how the website is written
    p_tags = soup.find_all("p")

    for tag in p_tags:
        # Inside a <p> tag, there's a Listen: section which contains the youtube URL
        if "Listen:" in tag.text:
            a_tags = tag.find_all("a")
            for a_tag in a_tags:
                if "YouTube" in a_tag.text:
                    youtube_url = a_tag.get("href")
                    return youtube_url


def switch(case):
    switcher = {
        'AMA #10: Benefits of Nature & “Grounding," Hearing Loss Research & Avoiding Altitude Sickness': lambda: "https://www.youtube.com/watch?v=eJU6Df_ffAE",
        "AMA #9: Kratom Risks, Does Infrared Sauna Work & Journaling Benefits": lambda: "https://www.youtube.com/watch?v=HoH93judXmE",
        "AMA #8: Balancing Caffeine, Decision Fatigue & Social Isolation": lambda: "https://www.youtube.com/watch?v=FE0lTEUa7EY",
        "AMA #7: Cold Exposure, Maximizing REM Sleep & My Next Scientific Studies": lambda: "https://www.youtube.com/watch?v=dicP_kA-RA0",
        "AMA #6: Eye Health, Why We Yawn & Increasing Motivation": lambda: "https://www.youtube.com/watch?v=uWV9a3zEaL4",
        "AMA #5: Intrusive Thoughts, CGMs, Behavioral Change, Naps & NSDR": lambda: "https://www.youtube.com/watch?v=cp9GXl9Qk_s",
        "AMA #4: Maintain Motivation, Improve REM Sleep, Set Goals, Manage Anxiety & More": lambda: "https://www.youtube.com/watch?v=S8nPJU9xkNw",
        "AMA #3: Adaptogens, Fasting & Fertility, Bluetooth/EMF Risks, Cognitive Load Limits & More": lambda: "https://www.youtube.com/watch?v=uak_dXHh6s4",
        "AMA #2: Improve Sleep, Reduce Sugar Cravings, Optimal Protein Intake, Stretching Frequency & More": lambda: "https://www.youtube.com/watch?v=vZ4kOr38JhY",
        "AMA #1: Leveraging Ultradian Cycles, How to Protect Your Brain, Seed Oils Examined and More": lambda: "https://www.youtube.com/watch?v=lsODSDmY4CY",
        "LIVE EVENT Q&A: Dr. Andrew Huberman Question & Answer in Los Angeles, CA": lambda: "https://www.youtube.com/watch?v=TO0WUTq5zYI",
        "LIVE EVENT Q&A: Dr. Andrew Huberman Question & Answer in Seattle, WA": lambda: "https://www.youtube.com/watch?v=2Ds1m5gflCI",
        "LIVE EVENT Q&A: Dr. Andrew Huberman Question & Answer in Portland, OR": lambda: "https://www.youtube.com/watch?v=3_auLYOilb8",
        "LIVE EVENT Q&A: Dr. Andrew Huberman Question & Answer in New York, NY": lambda: "https://www.youtube.com/watch?v=uwWOc_RqTBA",
        "Welcome to the Huberman Lab Podcast": lambda: "https://www.youtube.com/watch?v=4b6bwcWK6GE",
    }
    return switcher.get(case, lambda: None)()


def fetch_feed_data(rss_url):
    """Fetch feed data from the given RSS URL."""
    return feedparser.parse(rss_url)


def prepare_episode_data(feed):
    """Prepare a list of episode data from the given feed."""
    episodes = []
    for entry in feed.entries:
        try:
            title = remove_unicode_characters(entry.title)
            sanitized_title = sanitize_filename(title)
            summary = remove_unicode_characters(entry.summary)
            published = entry.published
            audio_url = next(
                link["href"] for link in entry["links"] if link["rel"] == "enclosure"
            )
            youtube_url = get_podcast_youtube_link(entry)
            episodes.append(
                {
                    "title": title,
                    "sanitized_title": sanitized_title,
                    "summary": summary,
                    "published": published,
                    "audio_url": audio_url,
                    "youtube_url": youtube_url,
                }
            )
        except StopIteration:
            logging.warning(
                f"Could not find an audio URL for episode '{entry.title}'. Skipping."
            )
        except Exception as e:
            logging.error(
                f"An error occurred while processing episode '{entry.title}': {e}"
            )
    return episodes


def main():
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Fetch and prepare episode data
    logging.info("Fetching Huberman Lab Podcast feed...")
    feed = fetch_feed_data(RSS_URL)

    logging.info("Preparing episode data...")
    episodes = prepare_episode_data(feed)

    # Write episode data to JSON file
    logging.info(f"Writing episode data to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(episodes, f, indent=4)

    logging.info("Done.")


if __name__ == "__main__":
    main()
