import gradio as gr
import pandas as pd
from sqlalchemy import create_engine
from sklearn.metrics.pairwise import cosine_similarity
import openai
import numpy as np
import faiss
import os
import re
import backoff

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


@backoff.on_exception(backoff.expo, openai.error.RateLimitError, max_tries=6)
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
                "content": "You are a health bot that answers only based on the context. If you don't know the answer, you can say 'I don't know'. ",
            },
            {"role": "user", "content": prompt},
            {
                "role": "user",
                "content": "Be detailed and clear in your explanation.",
            },
        ],
    )
    return completion.choices[0].message.content


def convert_to_link(url):
    return re.sub(r"(t=\d+)\.\d+", r"\1", url)


def chat_function(message, history):
    answer = chat_with_openai(message, history)

    context_df = get_context_to_question(message)
    context_df["episode_title"] = context_df["sanitized_title"]
    context_df = context_df[
        [
            "episode_title",
            "text",
            "youtube_url",
        ]
    ]

    context_df["youtube_url"] = context_df["youtube_url"].apply(convert_to_link)

    df_html = context_df.to_html(index=False)

    combined_response = f"{answer}<br><br><b>Sources:<b><br><p>{df_html}</p>"

    return combined_response


# Add a description at the top of the interface
description = """
<div>
    <p> Welcome to Huberman's Oracle! </p>
    <h2>🌟 Welcome to Huberman's Oracle!</h2>
    <p>🎧 <strong>What is this?:</strong> We are huge admirers of Andrew Huberman. To make the knowledge more accessible, Huberman's Oracle is crafted to answer your inquiries using data from indexed episodes of Huberman Podcasts. Just type your question and chat with Huberman! </p>
    <p>🔍 <strong> Retrieval Augmentation Generation:</strong> To complement the GPT model, we employ FAISS indexing technology for quick and precise similarity searches in high-dimensional spaces. This technology allows us to highlight the most pertinent episodes from Huberman Podcasts that relate to your questions.</p>
    <p>🔗 <strong>Easy References:</strong> For every answer we generate, we offer direct links to the relevant sections of Huberman Podcasts, complete with timestamps for easy reference.</p>
    <p>💖 <strong>Crafted with Love & Passion:</strong> This initiative serves as an tribute to Dr. Andrew Huberman's transformative work. We hope it empowers individuals on their quest for knowledge and self-betterment.</p>
    <p>👩‍💻 <strong>Developed by:</strong> 
    <a href="https://github.com/shitoshparajuli">@shitoshp</a>   
    <a href="https://github.com/pradhann">@pradhann</a> 
    </p>
    <p>💌 <strong>Want to Learn More or Chat?</strong> Feel free to <a href="https://www.linkedin.com/in/nripesh-pradhan-bb0b15132">send us a message</a>. We're always excited to connect with curious minds!</p>
</div>
"""


# Add example inputs and outputs
examples = [
    ["What is shingles - is it dangerous?", "Shingles can be dangerous..."],
    [
        "What is the importance of morning sunlight?",
        "Morning sunlight plays a vital role in setting our circadian rhythms, which govern functions like sleep, hormone release, and digestion. Experts recommend exposing your eyes to morning sunlight to help regulate these rhythms. [Source: Dr-Emily-Balcetis-Tools-for-Setting-Achieving-Goals.csv, Timestamp: 12:34]",
    ],
    [
        "How can I improve my focus?",
        "Improving focus can be achieved by manipulating your lighting conditions; a well-lit room can enhance focus and productivity. Elevating your screen above eye level can also induce a state of alertness. [Source: Optimizing-Workspace-for-Productivity-Focus-Creativity.csv, Timestamp: 24:56]",
    ],
    [
        "What are the benefits of deep breathing?",
        "Deep breathing can activate the parasympathetic nervous system, which helps to reduce stress and promote relaxation. It can also improve cognitive function and emotional regulation. [Source: Breathwork-for-Reducing-Stress.csv, Timestamp: 19:20]",
    ],
    [
        "How does exercise impact mental health?",
        "Regular exercise has been shown to improve mental well-being by releasing endorphins, which act as natural mood lifters. It can also help in reducing anxiety and depressive symptoms. [Source: Physical-Activity-and-Mental-Health.csv, Timestamp: 08:47]",
    ],
]

# Update the chat interface
chat_interface = gr.ChatInterface(
    fn=chat_function,
    title="Huberman's Oracle",
    description=description,
    examples=examples,
)
chat_interface.launch()
