# import spotipy
# from spotipy.oauth2 import SpotifyOAuth
# import os
# import json
# from datetime import datetime, timedelta
# from dotenv import load_dotenv
# import logging
# import random

# # Configure logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler(),
#         logging.FileHandler('spotify.log')
#     ]
# )
# logger = logging.getLogger(__name__)

# load_dotenv()
# # Cache setup
# CACHE_FILE = "data/spotify_cache.json"

# def load_cache():
#     try:
#         with open(CACHE_FILE, 'r') as f:
#             return json.load(f)
#     except (FileNotFoundError, json.JSONDecodeError):
#         return {}

# def save_cache(cache):
#     os.makedirs("data", exist_ok=True)
#     with open(CACHE_FILE, 'w') as f:
#         json.dump(cache, f)

# # Spotify auth
# def setup_spotify():
#     """
#     Set up Spotify client with authentication.
#     """
#     try:
#         # Get credentials from environment variables
#         client_id = os.getenv('SPOTIFY_CLIENT_ID')
#         client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
#         redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8080')
        
#         # Create Spotify client with required scopes
#         sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
#             client_id=client_id,
#             client_secret=client_secret,
#             redirect_uri=redirect_uri,
#             scope='user-library-read user-read-private'
#         ))
        
#         logger.info("Successfully created Spotify client")
#         return sp
#     except Exception as e:
#         logger.error(f"Error setting up Spotify: {str(e)}")
#         return None

# from utils.user_preferences import get_mood_preferences, add_preference

# def get_recommendations(sp, mood):
#     try:
#         logger.info(f"Getting recommendations for mood: {mood}")
        
#         # First check if we have user preferences for this mood
#         mood_preferences = get_mood_preferences(mood)
#         print(f"{mood} preferences:")
#         print(json.dumps(mood_preferences, indent=2))
#         print("Spotify client:", sp)
#         if mood_preferences:
#             logger.info(f"Found {len(mood_preferences)} preferred tracks for mood {mood}")
            
#             # Get tracks from user's library that match preferences
#             saved_tracks = sp.current_user_saved_tracks(limit=50)['items']
#             preferred_tracks = []
            
#             for saved_track in saved_tracks:
#                 # Check if this saved track is in user's preferences for this mood
#                 if any(p['track_id'] == saved_track['track']['id'] for p in mood_preferences):
#                     preferred_tracks.append(saved_track['track'])
            
#             if preferred_tracks:
#                 logger.info(f"Found {len(preferred_tracks)} matching preferred tracks")
#                 # Sort preferred tracks by confidence
#                 preferred_tracks.sort(
#                     key=lambda t: next(
#                         (p['confidence'] for p in mood_preferences 
#                          if p['track_id'] == t['id']),
#                         0.5  # Default confidence for new tracks
#                     ),
#                     reverse=True
#                 )
                
#                 # Get 2-3 preferred tracks (depending on how many are available)
#                 num_preferred = min(3, len(preferred_tracks))
#                 preferred_result = preferred_tracks[:num_preferred]
                
#                 # Get new tracks based on mood
#                 try:
#                     # Get recently played tracks
#                     saved_tracks = sp.current_user_recently_played(limit=50)['items']
#                     if not saved_tracks:
#                         logger.warning("No recently played tracks found")
#                         return preferred_result
                    
#                     # Get audio features for all tracks
#                     track_ids = [track['track']['id'] for track in saved_tracks]
#                     audio_features = sp.audio_features(track_ids)
                    
#                     # Filter tracks based on mood using audio features
#                     filtered_tracks = []
#                     for track, features in zip(saved_tracks, audio_features):
#                         if not features:
#                             continue
                            
#                         try:
#                             # Get track info
#                             track_info = track['track']
                            
#                             # Check if track is not in preferred tracks
#                             if any(p['track_id'] == track_info['id'] for p in preferred_tracks):
#                                 continue
                            
#                             # Filter based on mood and audio features
#                             if mood == "UPBEAT":
#                                 # For upbeat mood: high energy, high danceability, positive valence
#                                 if (features['energy'] > 0.6 and 
#                                     features['danceability'] > 0.6 and 
#                                     features['valence'] > 0.6):
#                                     filtered_tracks.append(track_info)
#                             elif mood == "CALMING":
#                                 # For calming mood: low energy, high acousticness, neutral valence
#                                 if (features['energy'] < 0.4 and 
#                                     features['acousticness'] > 0.5 and 
#                                     features['valence'] > 0.4):
#                                     filtered_tracks.append(track_info)
#                             else:  # MOTIVATIONAL
#                                 # For motivational mood: balanced energy, positive valence
#                                 if (features['energy'] > 0.5 and 
#                                     features['valence'] > 0.6):
#                                     filtered_tracks.append(track_info)
#                         except Exception as e:
#                             logger.warning(f"Error processing track {track_info.get('name', 'unknown')}: {str(e)}")
                    
#                     # Add up to 2 new tracks (if available)
#                     new_tracks = filtered_tracks[:2]
                    
#                     # Combine preferred and new tracks
#                     result = preferred_result + new_tracks
                    
#                     # If we don't have enough tracks, add random tracks
#                     if len(result) < 5:
#                         remaining = 5 - len(result)
#                         all_tracks = [t['track'] for t in saved_tracks]
#                         random_tracks = random.sample(all_tracks, min(remaining, len(all_tracks)))
#                         result.extend(random_tracks)
                    
#                     return result[:5]  # Return exactly 5 tracks
                    
#                 except Exception as e:
#                     logger.error(f"Error getting new tracks: {str(e)}")
#                     # If error getting new tracks, just return preferred tracks
#                     return preferred_result
        
#         # If no preferences, get tracks from Spotify
#         try:
#             # Get recently played tracks
#             saved_tracks = sp.current_user_recently_played(limit=5)['items']
#             print("Recently played tracks:")
#             print(json.dumps(saved_tracks, indent=2))
#             if not saved_tracks:
#                 logger.warning("No recently played tracks found")
#                 return []
            
#             # Get audio features for all tracks
#             track_ids = [track['track']['id'] for track in saved_tracks]
#             audio_features = sp.audio_features(track_ids)
            
#             # Filter tracks based on mood using audio features
#             filtered_tracks = []
#             for track, features in zip(saved_tracks, audio_features):
#                 if not features:
#                     continue
                    
#                 try:
#                     # Get track info
#                     track_info = track['track']
                    
#                     # Filter based on mood and audio features
#                     if mood == "UPBEAT":
#                         # For upbeat mood: high energy, high danceability, positive valence
#                         if (features['energy'] > 0.6 and 
#                             features['danceability'] > 0.6 and 
#                             features['valence'] > 0.6):
#                             filtered_tracks.append(track_info)
#                     elif mood == "CALMING":
#                         # For calming mood: low energy, high acousticness, neutral valence
#                         if (features['energy'] < 0.4 and 
#                             features['acousticness'] > 0.5 and 
#                             features['valence'] > 0.4):
#                             filtered_tracks.append(track_info)
#                     else:  # MOTIVATIONAL
#                         # For motivational mood: balanced energy, positive valence
#                         if (features['energy'] > 0.5 and 
#                             features['valence'] > 0.6):
#                             filtered_tracks.append(track_info)
#                 except Exception as e:
#                     logger.warning(f"Error processing track {track_info.get('name', 'unknown')}: {str(e)}")
            
#             # If we found matching tracks, return them
#             if filtered_tracks:
#                 logger.info(f"Found {len(filtered_tracks)} matching tracks for mood {mood}")
#                 return filtered_tracks[:5]  # Return top 5 matching tracks
            
#             # If no matching tracks, return random tracks from library
#             logger.info(f"No matching tracks found, returning random tracks from library")
#             return [track['track'] for track in random.sample(saved_tracks, min(5, len(saved_tracks)))]
            
#         except Exception as e:
#             logger.error(f"Error getting tracks from library: {str(e)}")
#             # If all else fails, just return random tracks
#             saved_tracks = sp.current_user_saved_tracks(limit=50)['items']
#             return [track['track'] for track in random.sample(saved_tracks, min(5, len(saved_tracks)))]
            
#     except Exception as e:
#         logger.error(f"Error in get_recommendations: {str(e)}")
#         logger.warning(f"Returning empty list due to error: {str(e)}")
#         return []  # Return empty list if no results available

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
