import json
import os
from datetime import datetime
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

PREFERENCES_FILE = 'user_preferences.json'


def load_preferences() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load user preferences from JSON file.
    Returns empty dictionary if file doesn't exist.
    """
    try:
        if not os.path.exists(PREFERENCES_FILE):
            return {}
        
        with open(PREFERENCES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading preferences: {str(e)}")
        return {}


def save_preferences(preferences: Dict[str, List[Dict[str, Any]]]):
    """
    Save user preferences to JSON file.
    """
    try:
        with open(PREFERENCES_FILE, 'w') as f:
            json.dump(preferences, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving preferences: {str(e)}")


def add_preference(mood: str, track_id: str, track_name: str, artist_name: str) -> bool:
    """
    Add a new track preference for a specific mood.
    """
    try:
        logger.info(f"Adding preference for mood {mood}: {track_name} by {artist_name}")
        
        # Load existing preferences
        preferences = load_preferences()
        
        # Initialize mood list if it doesn't exist
        if mood not in preferences:
            preferences[mood] = []
        
        # Add new preference if it doesn't already exist
        if not any(p['track_id'] == track_id for p in preferences[mood]):
            preferences[mood].append({
                'track_id': track_id,
                'track_name': track_name,
                'artist_name': artist_name,
                'timestamp': datetime.now().isoformat(),
                'confidence': 1.0  # Start with high confidence
            })
            
            # Save updated preferences
            save_preferences(preferences)
            logger.info(f"Successfully added preference for {track_name} in {mood} mood")
            return True
        
        logger.info(f"Track {track_name} already exists in {mood} mood preferences")
        return False
    except Exception as e:
        logger.error(f"Error adding preference: {str(e)}")
        return False


def update_preference(mood: str, track_id: str, feedback: str) -> bool:
    """
    Update a track preference based on user feedback.
    """
    try:
        preferences = load_preferences()
        
        if mood in preferences:
            for pref in preferences[mood]:
                if pref['track_id'] == track_id:
                    # Update confidence based on feedback
                    if feedback == 'like':
                        pref['confidence'] = min(1.0, pref.get('confidence', 0.5) + 0.2)
                    else:  # dislike
                        pref['confidence'] = max(0.0, pref.get('confidence', 0.5) - 0.2)
                    
                    # Save updated preferences
                    save_preferences(preferences)
                    logger.info(f"Updated confidence for {pref['track_name']} in {mood} mood")
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Error updating preference: {str(e)}")
        return False


def get_mood_preferences(mood: str, min_confidence: float = 0.4) -> List[Dict[str, Any]]:
    """
    Get all track preferences for a specific mood with confidence above threshold.
    """
    try:
        preferences = load_preferences()
        mood_prefs = preferences.get(mood, [])
        
        # Filter by confidence
        return [p for p in mood_prefs if p.get('confidence', 0.0) >= min_confidence]
    except Exception as e:
        logger.error(f"Error getting mood preferences: {str(e)}")
        return []


def get_track_mood(track_id: str) -> List[str]:
    """
    Get the mood(s) a track is preferred for.
    """
    try:
        preferences = load_preferences()
        moods = []
        for mood, tracks in preferences.items():
            if any(t['track_id'] == track_id for t in tracks):
                moods.append(mood)
        return moods
    except Exception as e:
        logger.error(f"Error getting track mood: {str(e)}")
        return []
