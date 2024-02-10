"""
engine.py

This module provides core functionalities for the Flask application, including interactions with the OpenAI API,
FAISS index querying, and utility functions for processing and formatting data. It is designed to support the
application's needs for fetching embeddings, generating responses based on context, and formatting data for output.

Dependencies:
- Flask for the web application framework.
- Pandas for data manipulation.
- SQL Alchemy for database operations.
- OpenAI for accessing the OpenAI API.
- NumPy for numerical operations.
- FAISS for efficient similarity search in large datasets.
- Python standard libraries: os, re, backoff for retrying operations.
"""

from flask import current_app


from config import Config
import pandas as pd
from sqlalchemy import create_engine
import openai
import numpy as np
import faiss
import re
import backoff
from errors import ProcessingError, OpenAIError

# Initialize external services with configurations
openai.api_key = Config.OPENAI_API_KEY
engine = create_engine(Config.DATABASE_URI)
index = faiss.read_index("data/processed/faiss_index.index")


def openai_health_check():
    """Raises an exception if OpenAI API isn't available"""
    openai.Model.list()


def get_embeddings(line):
    """
    Fetches embeddings for a given line of text using the OpenAI API.

    Parameters:
    - line (str): The text line for which embeddings are to be fetched.

    Returns:
    - list: The embedding vector for the given line of text.
    """
    return openai.Embedding.create(input=[line], model="text-embedding-ada-002")[
        "data"
    ][0]["embedding"]


def get_context_response(question):
    """
    Retrieves relevant context for a given question by querying the FAISS index with the question's embedding.

    Parameters:
    - question (str): The question for which context is being sought.

    Returns:
    - DataFrame: A pandas DataFrame containing the relevant context for the question.
    """
    try:
        query_embedding = (
            np.array(get_embeddings(question)).astype("float32").reshape(1, -1)
        )
        faiss.normalize_L2(query_embedding)
        distances, indices = index.search(query_embedding, 5)
        return pd.read_sql_table("docs", engine).iloc[indices.flatten()]
    except Exception as e:
        current_app.logger.error(f"Error in get_context_response: {e}")
        raise ProcessingError(
            f"Error occurred while fetching context response: {e}", e.__class__.__name__
        )


def _convert_to_link(url):
    """
    Converts a YouTube URL to a shorter format by removing milliseconds from the timestamp.

    Parameters:
    - url (str): The original YouTube URL.

    Returns:
    - str: The converted YouTube URL.
    """
    return re.sub(r"(t=\d+)\.\d+", r"\1", url)


def format_context_response(context_df):
    """
    Formats context data into a structured list of dictionaries for easier JSON serialization.

    Parameters:
    - context_df (DataFrame): A pandas DataFrame containing context information.

    Returns:
    - list: A list of dictionaries, each representing a piece of context information.
    """
    try:
        return [
            {
                "episode_title": row["sanitized_title"],
                "relevant_snippet": re.sub("\n", " ", row["text"]),
                "youtube_url": _convert_to_link(row["youtube_url"]),
            }
            for _, row in context_df.iterrows()
        ]
    except Exception as e:
        current_app.logger.error(f"Error in format_context_response: {e}")
        raise ProcessingError(
            f"Error occurred while formatting context response: {e}", e.__class__.__name__
        )


@backoff.on_exception(backoff.expo, openai.error.RateLimitError, max_tries=6)
def get_openai_response(question, history=""):
    """
    Generates a response from OpenAI's GPT model based on a given question and previous conversation history.

    Parameters:
    - question (str): The question to ask the model.
    - history (str): A string representing the previous conversation history.

    Returns:
    - str: The model's response to the question.
    """
    try:
        context_df = get_context_response(question)
        prompt = f"Previous Conversation: {' '.join(history)}\nQuestion: {question}\nContext:\n{' '.join(context_df['text'])}"
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except openai.error.OpenAIError as error:
        current_app.logger.error(
            f"Error occurred while making the request to OpenAI: {error}"
        )
        raise OpenAIError(
            f"Error occurred while making the request to OpenAI: {error}",
            error.__class__.__name__,
        )
    except Exception as e:
        current_app.logger.error(f"Error in get_humberman_response: {e}")
        raise


def get_humberman_response(message, history):
    """
    Orchestrates the process of fetching a response for a given message and history,
    involving OpenAI response generation and context response formatting.

    Parameters:
    - message (str): The message for which a response is sought.
    - history (list): A list of previous messages or conversation history.

    Returns:
    - dict: A dictionary containing the OpenAI response and formatted context responses.
    """
    openai_response = get_openai_response(message, history)
    context_df = get_context_response(message)
    formatted_context_responses = format_context_response(context_df)
    return {
        "open_ai_response": openai_response,
        "context_responses": formatted_context_responses,
    }
