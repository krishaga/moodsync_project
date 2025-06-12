import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import logging
import random

from utils.user_preferences import get_mood_preferences, add_preference

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('spotify.log')
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Spotify authentication setup
def setup_spotify():
    try:
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:3000/callback')

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope='user-library-read user-read-private user-read-recently-played'
        ))
        logger.info("Spotify client created successfully")
        return sp
    except Exception as e:
        logger.error(f"Spotify setup failed: {e}")
        return None

def track_matches_mood(features, mood):
    """Match tracks to expanded mood categories based on audio features
    
    Args:
        features: Spotify audio features for a track
        mood: The mood category to match against
        
    Returns:
        bool: Whether the track matches the mood
    """
    if not features:
        return False
    
    # Define mood-specific audio feature criteria
    mood_criteria = {
        "UPBEAT": lambda f: f['valence'] > 0.6 and f['energy'] > 0.6 and f['tempo'] > 100,
        
        "CALMING": lambda f: f['valence'] > 0.4 and f['energy'] < 0.5 and f['acousticness'] > 0.4,
        
        "MELANCHOLY": lambda f: f['valence'] < 0.4 and f['energy'] < 0.6 and f['mode'] == 0,  # Minor key
        
        "ROMANTIC": lambda f: f['valence'] > 0.5 and f['energy'] < 0.6 and f['acousticness'] > 0.3 and f['instrumentalness'] < 0.5,
        
        "MOTIVATIONAL": lambda f: f['energy'] > 0.7 and f['tempo'] > 120 and f['valence'] > 0.5,
        
        "INTENSE": lambda f: f['energy'] > 0.8 and f['loudness'] > -6 and f['valence'] < 0.6,
        
        "FOCUSED": lambda f: 0.3 < f['energy'] < 0.7 and f['instrumentalness'] > 0.4 and f['speechiness'] < 0.1
    }
    
    # Check if the mood is in our criteria dictionary
    if mood in mood_criteria:
        return mood_criteria[mood](features)
    
    # Fallback for unrecognized moods
    logger.warning(f"Unrecognized mood: {mood}, using default criteria")
    return True  # Default to include if mood not recognized False

# Get filtered tracks by mood
def filter_tracks_by_mood(sp, tracks, mood, excluded_ids=set()):
    try:
        # Import Streamlit and cleanup function
        import streamlit as st
        from app import cleanup_expired_dislikes, should_exclude_track
        
        # Cleanup expired dislikes (older than 2 hours)
        if hasattr(st, 'session_state') and hasattr(st.session_state, 'mood_disliked_tracks'):
            cleanup_expired_dislikes(hours=2)
        
        # Build exclusion set: regular + disliked in last 2 hours
        all_excluded_ids = set(excluded_ids) if excluded_ids else set()
        if hasattr(st, 'session_state') and hasattr(st.session_state, 'mood_disliked_tracks'):
            if mood in st.session_state.mood_disliked_tracks:
                for track_id in list(st.session_state.mood_disliked_tracks[mood].keys()):
                    if should_exclude_track(mood, track_id, cooldown_hours=2):
                        all_excluded_ids.add(track_id)
                        logger.info(f"Excluding mood-specific disliked track {track_id} for {mood}")
        
        # Filter out excluded tracks first
        track_ids = []
        filtered_tracks = []
        for track in tracks:
            track_info = track['track']
            if track_info['id'] not in all_excluded_ids:
                track_ids.append(track_info['id'])
                filtered_tracks.append(track)
        
        if not track_ids:
            return []
        features = sp.audio_features(track_ids)
        mood_tracks = []
        for item, feature in zip(filtered_tracks, features):
            if not feature:
                continue
            track_info = item['track']
            if track_matches_mood(feature, mood):
                mood_tracks.append(track_info)
        # Shuffle to add variety
        import random
        random.shuffle(mood_tracks)
        return mood_tracks
    except Exception as e:
        logger.error(f"Error filtering tracks by mood: {e}")
        return []

# Main function to get recommendations
def get_recommendations(sp, mood):
    try:
        logger.info(f"Fetching recommendations for mood: {mood}")
        mood_prefs = get_mood_preferences(mood)
        preferred_tracks = []
        preferred_ids = set()
        all_track_ids = set()  # Track all IDs to prevent duplicates

        # Get user's preferred tracks for this mood
        if mood_prefs:
            saved_tracks = sp.current_user_saved_tracks(limit=50)['items']
            for item in saved_tracks:
                track_id = item['track']['id']
                for pref in mood_prefs:
                    if track_id == pref['track_id'] and track_id not in all_track_ids:
                        preferred_tracks.append(item['track'])
                        preferred_ids.add(track_id)
                        all_track_ids.add(track_id)
                        break

            # Sort by confidence score
            preferred_tracks = sorted(
                preferred_tracks,
                key=lambda t: next((p['confidence'] for p in mood_prefs if p['track_id'] == t['id']), 0),
                reverse=True
            )
            preferred_tracks = preferred_tracks[:3]  # Get top 3 preferred tracks

        # Get recently played tracks that match the mood
        recent_tracks = sp.current_user_recently_played(limit=50)['items']
        
        # Filter tracks by mood and exclude already selected tracks
        new_mood_tracks = []
        mood_filtered = filter_tracks_by_mood(sp, recent_tracks, mood, excluded_ids=all_track_ids)
        
        # Add up to 2 mood-matching tracks, avoiding duplicates
        for track in mood_filtered:
            if track['id'] not in all_track_ids and len(new_mood_tracks) < 2:
                new_mood_tracks.append(track)
                all_track_ids.add(track['id'])

        # Combine preferred and new tracks
        result_tracks = preferred_tracks + new_mood_tracks

        # If we still need more tracks to reach 5
        if len(result_tracks) < 5:
            needed = 5 - len(result_tracks)
            
            # Try to get tracks from user's saved library first
            saved_tracks = sp.current_user_saved_tracks(limit=50)['items']
            additional_tracks = []
            
            for item in saved_tracks:
                track = item['track']
                if track['id'] not in all_track_ids:
                    additional_tracks.append(track)
                    all_track_ids.add(track['id'])
                    if len(additional_tracks) >= needed:
                        break
            
            # If still not enough, use recently played tracks
            if len(additional_tracks) < needed:
                still_needed = needed - len(additional_tracks)
                all_recent = [t['track'] for t in recent_tracks if t['track']['id'] not in all_track_ids]
                
                if all_recent:
                    # Use random.sample only if we have enough tracks
                    sample_size = min(still_needed, len(all_recent))
                    if sample_size > 0:
                        random_picks = random.sample(all_recent, sample_size)
                        for track in random_picks:
                            additional_tracks.append(track)
                            all_track_ids.add(track['id'])
            
            result_tracks += additional_tracks

        # Final check for duplicates (safety check)
        final_tracks = []
        final_track_ids = set()
        
        for track in result_tracks:
            if track['id'] not in final_track_ids:
                final_tracks.append(track)
                final_track_ids.add(track['id'])
                if len(final_tracks) >= 5:
                    break

        logger.info(f"Returning {len(final_tracks)} recommendations with {len(final_track_ids)} unique tracks")
        return final_tracks[:5]

    except Exception as e:
        logger.error(f"Error in get_recommendations: {e}")
        return []
