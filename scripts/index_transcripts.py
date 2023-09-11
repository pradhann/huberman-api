import json
import logging
import os
from multiprocessing import Pool

import faiss
import numpy as np
import openai
import pandas as pd
from tqdm import tqdm
import math

# Gloabls
csv_files_dir = "data/transcribed/youtube"
JSON_PATH = "HubermanPodcastEpisodes.json"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set OpenAI API key
openai.api_key = "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"

# Define the embedding type
embedding_type = np.dtype(
    [
        ("embedding", np.float64, (1536,)),
        ("text", str, 10000),
        ("start", str, 50),
        ("sanitized_title", str, 100),
        ("youtube_url", str, 100),
    ]
)


def get_embeddings(line: str):
    """
    Get embeddings for a given line of text using OpenAI API.

    Args:
        line (str): The input text.

    Returns:
        np.ndarray: The embeddings for the input text.
    """
    return openai.Embedding.create(input=[line], model="text-embedding-ada-002")[
        "data"
    ][0]["embedding"]


def process_transcript(episode):
    """
    Process a transcript and generate embeddings.

    Args:
        transcript (dict): The transcript data.

    Returns:
        np.ndarray: The embeddings for the transcript.
    """
    embeddings = []
    logger.info(f"Processing transcript: {episode['sanitized_title']}")

    # Load the transcript from the sanitized title
    sanitized_title = episode["sanitized_title"]
    csv_file_path = f"{csv_files_dir}/{sanitized_title}.csv"

    if not os.path.exists(csv_file_path):
        return None

    df = pd.read_csv(csv_file_path)

    # Add tqdm progress bar
    for index, row in tqdm(df.iterrows(), total=len(df)):
        embed_text = row["text"]
        start_time = row["start"]
        start_time_floor = math.floor(start_time)
        youtube_url = f"{episode['youtube_url']}?t={start_time}"
        arr = (
            get_embeddings(embed_text),
            embed_text,
            start_time,
            sanitized_title,
            youtube_url,
        )
        embeddings.append(arr)
    return np.array(embeddings, dtype=embedding_type)


def save_embeddings(embeddings):
    """
    Save the embeddings to a file.

    Args:
        embeddings (np.ndarray): The embeddings to be saved.
    """
    np.save("data/processed/embeddings.npy", embeddings, allow_pickle=True)


def save_faiss_index(embeddings):
    """
    Save the faiss index to a file.

    Args:
        embeddings (np.ndarray): The embeddings to be saved.
    """
    embeddings = [x[0] for x in embeddings]
    embeddings_np = np.vstack(embeddings).astype("float32")
    faiss.normalize_L2(embeddings_np)
    faiss_index = faiss.IndexFlatIP(embeddings_np.shape[1])
    faiss_index.add(embeddings_np)
    faiss.write_index(faiss_index, "data/processed/faiss_index.index")


def main():
    # Load original embeddings
    original_embeddings_path = "data/processed/embeddings.npy"
    if os.path.exists(original_embeddings_path):
        original_embeddings = np.load(original_embeddings_path, allow_pickle=True)
    else:
        original_embeddings = np.empty((0,), dtype=embedding_type)

    completed_episodes = list(set([x["sanitized_title"] for x in original_embeddings]))

    # Load transcript data
    with open(JSON_PATH, "r") as f:
        episodes = json.load(f)

    new_episodes = [
        episode
        for episode in episodes
        if episode["sanitized_title"] not in completed_episodes
    ]

    embeddings = []

    # Process transcripts in parallel
    with Pool() as pool:
        for result in tqdm(
            pool.imap_unordered(process_transcript, new_episodes),
            total=len(new_episodes),
        ):
            if result is not None:
                embeddings.append(result)

    # Concatenate all arrays into a single numpy array
    if embeddings:
        new_embeddings = np.concatenate(embeddings)
        final_embeddings = np.concatenate([original_embeddings, new_embeddings])
    else:
        final_embeddings = original_embeddings

    save_embeddings(final_embeddings)
    save_faiss_index(final_embeddings)


if __name__ == "__main__":
    main()
