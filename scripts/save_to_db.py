import os
from datetime import datetime

import numpy as np
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base

# Get the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct paths
db_dir = os.path.join(script_dir, "../data/processed")
db_path = os.path.join(db_dir, "embeddings.db")

# Create the directory if it doesn't exist
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# Load the embeddings from the file
embeddings_file_path = os.path.join(script_dir, "../data/processed/embeddings.npy")
embeddings = np.load(embeddings_file_path, allow_pickle=True)

# Create the database engine
engine = create_engine(f"sqlite:///{db_path}")

Base = declarative_base()


class Document(Base):
    __tablename__ = "docs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding = Column(Vector(1536))
    text = Column(String)
    start = Column(String)
    sanitized_title = Column(String)
    youtube_url = Column(String)
    updated_at = Column(String)


# Drop and create the table
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

documents = [
    Document(
        embedding=embedding[0],
        text=embedding[1],
        start=embedding[2],
        sanitized_title=embedding[3],
        youtube_url=embedding[4],
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    for embedding in embeddings
]

# Create a session and insert the documents
session = Session(engine)
session.add_all(documents)
session.commit()
