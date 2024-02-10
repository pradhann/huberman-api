# Huberman Lab API 🧠

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg?style=flat&logo=python)
![Flask](https://img.shields.io/badge/Flask-v1.1.x-orange.svg?style=flat&logo=flask)
![build](https://img.shields.io/badge/build-passing-brightgreen.svg?style=flat)
![license](https://img.shields.io/github/license/pradhann/huberman-api.svg?style=flat)
![OpenAI](https://img.shields.io/badge/OpenAI-API-blueviolet?style=flat&logo=openai)

The Huberman Lab API is a Flask-powered RESTful API designed to serve insights and data extracted from the Huberman Lab Podcast. Utilizing advanced machine learning models via the OpenAI API, this service aims to provide quick access to podcast content, enabling users to query specific topics and receive contextually relevant responses.

## Overview 🌟

The Huberman Lab, hosted by Dr. Andrew Huberman, explores science and science-based tools for everyday life. This API indexes podcast episodes to allow for an interactive exploration of its rich content, offering a unique way to access information on neuroscience, health, and personal development.

### Features ✨

- **Full-text Search** 🔍: Quickly find podcast segments relevant to your query.
- **Contextual Insights** 💡: Get detailed responses based on the semantic understanding of the content.
- **Episode Recommendations** 🎧: Discover episodes related to your interests.
- **Easy Integration** 🛠️: Designed for developers, offering straightforward endpoints for integrating with applications.

## Getting Started 🚀

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.7+
- pip
- Virtualenv (optional)

### Installation

Clone the repository:

```bash
git clone https://github.com/pradhann/huberman-api.git
cd huberman-api
```

Create and activate a virtual environment (optional):

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Configuration
Add your OPEN_AI_API_KEY


## Running Locally
Start the Flask application:

```bash
flask run | python app.py
```

The API should now be accessible at http://localhost:5000/.

## Usage 📘
### Health Check
Check the API's health:

```bash
GET /health_check
```

### Querying the API
Request insights on a specific topic:

```bash

POST /ask_huberman
Content-Type: application/json

{
  "message": "How does sunlight affect sleep?",
  "history": []
}
```

## Deployment 🌐
This API is deployed on Fly.io. For details on deploying to Fly.io, refer to their official documentation.


## Acknowledgments 💖
Dr. Andrew Huberman for the inspiring content.
OpenAI for the powerful GPT models.
Fly.io for the seamless deployment experience.