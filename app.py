import gradio as gr
import pandas as pd
from sqlalchemy import create_engine
from sklearn.metrics.pairwise import cosine_similarity
import openai
import numpy as np
import faiss
import os
import re

# Load the OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Create the database engine
engine = create_engine("sqlite:///data/processed/embeddings.db")

# Load the DataFrame from the "docs" table
df = pd.read_sql_table("docs", engine)

# Load the saved faiss index
index = faiss.read_index("data/processed/faiss_index.index")


def get_embeddings(line):
    return openai.Embedding.create(input=[line], model="text-embedding-ada-002")[
        "data"
    ][0]["embedding"]


def get_context_to_question(question):
    query_embedding = get_embeddings(question)  # reshape the vector
    query_embedding = np.array(query_embedding).astype("float32")
    # Normalize the vector before querying faiss index
    query_embedding = query_embedding.reshape(1, -1)  # reshape the vector
    faiss.normalize_L2(query_embedding)
    # Query the faiss index
    k = 5
    distances, indices = index.search(query_embedding, k)
    # Collect and return the results
    context_df = df.iloc[indices.flatten()]
    return context_df


def chat_with_openai(question, history=""):
    context_df = get_context_to_question(question)
    context = "\n".join(context_df["text"])
    history_summary = [conversation[1] for conversation in history]
    history_summary.reverse()  # Reverse the list to get the latest conversation first

    # Calculate the total number of words in history_string
    word_count = sum(len(message.split()) for message in history_summary)

    # Check if adding the latest message will exceed the word limit
    if word_count + len(question.split()) <= 1000:
        history_summary.append(question)

    # Truncate history_summary to contain at most 1000 words
    if len(history_summary) > 1000:
        history_summary = history_summary[-1000:]

    # Reverse the history_summary list to get the latest conversation last
    history_summary.reverse()

    history_string = "\n".join(history_summary)
    prompt = f"""
            Previous Conversation: {history_string}
            Question: {question}
            Context:
            {context}
        """
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a health bot that answers based on the context. If you don't know the answer, you can say 'I don't know'. ",
            },
            {"role": "user", "content": prompt},
            {
                "role": "user",
                "content": "Be detailed and clear in your explanation. Cite sourcers to back your answer. Use bullet points to make your answer easier to read.",
            },
        ],
    )
    return completion.choices[0].message.content


def convert_to_link(url):
    return re.sub(r"(t=\d+)\.\d+", r"\1", url)


def chat_function(message, history):
    answer = chat_with_openai(message, history)

    context_df = get_context_to_question(message)
    context_df = context_df[
        [
            "sanitized_title",
            "text",
            "youtube_url",
        ]
    ]

    context_df["youtube_url"] = context_df["youtube_url"].apply(convert_to_link)

    df_html = context_df.to_html(classes="table table-striped")

    combined_response = f"{answer}<br><br><b>Sources:<b><br><p>{df_html}</p>"

    return combined_response


chat_interface = gr.ChatInterface(fn=chat_function, title="Huberman's Oracle")
chat_interface.launch()
