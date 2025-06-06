# MoodSync

![Dashboard Screenshot](/static/image.png)

## Overview

**MoodSync** is an intelligent music recommendation system that suggests songs from your own Spotify playlists based on the mood detected in the text you provide. By leveraging sentiment analysis and learning from your feedback, MoodSync creates a personalized listening experience that adapts to your emotional state and preferences over time.

## How It Works

1. **Input Your Mood**: Enter a text describing how you feel (e.g., "I feel happy and energetic today!").
2. **Mood Detection**: The app uses advanced sentiment analysis (powered by transformer models and keyword matching) to classify your mood into categories like Upbeat, Calming, Melancholy, Romantic, Motivational, Intense, or Focused.
3. **Personalized Recommendations**: Songs are recommended from your Spotify library and recently played tracks that best match your detected mood.
4. **Interactive Feedback**: For each recommendation, you can provide feedback (Like, Dislike, Skip). If you dislike a song for a specific mood, MoodSync learns not to suggest it again in similar situations, improving recommendations over time.
5. **Continuous Learning**: The system updates your preferences, tracks your feedback, and adapts future recommendations based on your evolving musical tastes and moods.

## Features

- **Spotify Integration**: Connects to your Spotify account to access your playlists, saved tracks, and listening history.
- **Sentiment & Mood Analysis**: Uses NLP models (transformers, BERTweet) and custom keyword mapping for robust mood detection.
- **Adaptive Learning**: Remembers your feedback for different moods and avoids recommending disliked tracks in the future.
- **User Preferences Storage**: Stores your mood-song preferences locally for fast and private adaptation.
- **Dashboard**: Intuitive Streamlit dashboard with embedded Spotify player, audio feature visualization, and easy feedback buttons.
- **Privacy-First**: All user preferences are stored locally; your Spotify credentials are managed securely with `.env` variables.

## Tech Stack & Dependencies

- **Python** (core language)
- **Streamlit** (interactive dashboard)
- **Transformers** (`transformers`, `torch`)
- **Spotipy** (Spotify Web API integration)
- **Gradio** (optional for alternative UI)
- **Pandas, Numpy** (data handling)
- **python-dotenv** (environment variable management)

See [`requirements.txt`](requirements.txt) for full package versions.

## File Structure

- `app.py` — Main Streamlit dashboard and app logic
- `utils/`
  - `mood_analyzer.py` — Mood detection and sentiment analysis
  - `spotify_helper.py` — Spotify API integration and track filtering
  - `user_preferences.py` — User feedback management and learning
- `user_preferences.json` — Stores user feedback and preferences
- `.env` — Spotify API credentials (not included in repo)
- `static/` — For dashboard images and resources

## Setup & Usage

1. **Clone the repo**
    ```bash
    git clone <repo-url>
    cd moodsync_project
    ```
2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
3. **Set up Spotify API credentials**
    - Create a `.env` file in the project root:
      ```env
      SPOTIFY_CLIENT_ID=your_spotify_client_id
      SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
      SPOTIFY_REDIRECT_URI=http://localhost:8080
      ```
4. **Run the app**
    ```bash
    streamlit run app.py
    ```

---

**MoodSync** — Personalized music for every mood.
