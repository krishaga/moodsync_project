import streamlit as st
from utils.mood_analyzer import detect_mood
from utils.spotify_helper import setup_spotify, get_recommendations
from utils.user_preferences import add_preference, update_preference
import os
from dotenv import load_dotenv
import time
import logging
import random
from datetime import datetime, timedelta

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

# Config
load_dotenv()
st.set_page_config(page_title="MoodSync", page_icon="🎵")

# Initialize session state for mood, tracks, rejected tracks, and current mood text
if 'mood' not in st.session_state:
    st.session_state.mood = ""
if 'mood_text' not in st.session_state:
    st.session_state.mood_text = ""
if 'tracks' not in st.session_state:
    st.session_state.tracks = []
if 'rejected_tracks' not in st.session_state:
    st.session_state.rejected_tracks = set()
# Dictionary to track mood-specific disliked tracks with timestamps
if 'mood_disliked_tracks' not in st.session_state:
    st.session_state.mood_disliked_tracks = {}

# Spotify auth
@st.cache_resource
def init_spotify():
    return setup_spotify()

def add_mood_disliked_track(mood, track_id):
    """Add a track to the mood-specific disliked tracks with a timestamp"""
    if mood not in st.session_state.mood_disliked_tracks:
        st.session_state.mood_disliked_tracks[mood] = {}
    st.session_state.mood_disliked_tracks[mood][track_id] = datetime.now()
    logger.info(f"Added track {track_id} to disliked tracks for mood {mood}")

def cleanup_expired_dislikes(hours=2):
    """Remove disliked tracks older than the cooldown period (default 2 hours)"""
    now = datetime.now()
    for mood in list(st.session_state.mood_disliked_tracks.keys()):
        to_remove = []
        for track_id, ts in st.session_state.mood_disliked_tracks[mood].items():
            if now - ts > timedelta(hours=hours):
                to_remove.append(track_id)
        for track_id in to_remove:
            del st.session_state.mood_disliked_tracks[mood][track_id]
        # Remove mood key if empty
        if not st.session_state.mood_disliked_tracks[mood]:
            del st.session_state.mood_disliked_tracks[mood]

def should_exclude_track(mood, track_id, cooldown_hours=2):
    """Check if a track should be excluded based on recent dislikes (default 2 hours)."""
    if mood not in st.session_state.mood_disliked_tracks:
        return False
    if track_id not in st.session_state.mood_disliked_tracks[mood]:
        return False
    disliked_time = st.session_state.mood_disliked_tracks[mood][track_id]
    if datetime.now() - disliked_time < timedelta(hours=cooldown_hours):
        logger.info(f"Excluding recently disliked track {track_id} for mood {mood}")
        return True
    return False

def get_replacement_track(sp, idx, track):
    """Helper function to get a replacement track and update session state"""
    try:
        # Get all current track IDs to avoid duplicates
        current_track_ids = set(t['id'] for t in st.session_state.tracks)
        
        # Add the track we're replacing to rejected tracks
        track_id_to_replace = track['id']
        st.session_state.rejected_tracks.add(track_id_to_replace)
        
        # Ensure we're using the current mood
        current_mood = st.session_state.mood
        logger.info(f"Finding replacement track for mood: {current_mood}")
        
        # Try multiple sources for replacement tracks
        replacement_found = False
        
        # 1. First try: Get mood-matching tracks from recently played
        if not replacement_found:
            recent_tracks = sp.current_user_recently_played(limit=50)['items']
            
            # Filter by mood and exclude rejected and current tracks
            from utils.spotify_helper import filter_tracks_by_mood
            mood_tracks = filter_tracks_by_mood(sp, recent_tracks, current_mood, 
                                             excluded_ids=st.session_state.rejected_tracks.union(current_track_ids))
            
            if mood_tracks:
                replacement_track = random.choice(mood_tracks)
                st.session_state.tracks[idx] = replacement_track
                st.success(f"Replaced with: {replacement_track['name']} by {replacement_track['artists'][0]['name']}")
                replacement_found = True
        
        # 2. Second try: Get any non-rejected tracks from recently played
        if not replacement_found:
            recent_tracks = sp.current_user_recently_played(limit=50)['items']
            new_tracks = [t['track'] for t in recent_tracks 
                        if t['track']['id'] not in st.session_state.rejected_tracks 
                        and t['track']['id'] not in current_track_ids]
            
            if new_tracks:
                replacement_track = random.choice(new_tracks)
                st.session_state.tracks[idx] = replacement_track
                st.success(f"Replaced with: {replacement_track['name']} by {replacement_track['artists'][0]['name']}")
                replacement_found = True
        
        # 3. Third try: Get tracks from user's saved library
        if not replacement_found:
            saved_tracks = sp.current_user_saved_tracks(limit=50)['items']
            library_tracks = [item['track'] for item in saved_tracks 
                           if item['track']['id'] not in st.session_state.rejected_tracks 
                           and item['track']['id'] not in current_track_ids]
            
            if library_tracks:
                replacement_track = random.choice(library_tracks)
                st.session_state.tracks[idx] = replacement_track
                st.success(f"Replaced with: {replacement_track['name']} by {replacement_track['artists'][0]['name']}")
                replacement_found = True
        
        if replacement_found:
            st.rerun()
        else:
            st.error("No more tracks available to recommend")
            # Clear rejected tracks as a last resort to allow more recommendations
            st.session_state.rejected_tracks = set([track_id_to_replace])
            
    except Exception as e:
        logger.error(f"Error replacing track: {e}")
        st.error(f"Error replacing track: {str(e)}")

def main():
    st.title("🎵 MoodSync")
    st.write("Share how you're feeling and get music recommendations!")
    
    # Set up sidebar with app info and mood display
    st.sidebar.title("🎵 MoodSync")  
    st.sidebar.markdown("### Your Music Mood Companion")
    st.sidebar.markdown("---")
    
    # Display current mood with emoji if one is set
    if st.session_state.mood:
        mood_emojis = {
            "UPBEAT": "😄 UPBEAT",
            "CALMING": "😌 CALMING",
            "MELANCHOLY": "😢 MELANCHOLY",
            "ROMANTIC": "❤️ ROMANTIC",
            "MOTIVATIONAL": "💪 MOTIVATIONAL",
            "INTENSE": "🔥 INTENSE",
            "FOCUSED": "🧠 FOCUSED"
        }
        mood_display = mood_emojis.get(st.session_state.mood, st.session_state.mood)
        st.sidebar.markdown(f"### Current Mood: {mood_display}")
        
        # Add mood description
        mood_descriptions = {
            "UPBEAT": "Energetic, happy, and cheerful music to lift your spirits.",
            "CALMING": "Peaceful, relaxing tunes to help you unwind and destress.",
            "MELANCHOLY": "Emotional, reflective songs that resonate with sadness or nostalgia.",
            "ROMANTIC": "Love songs and tender melodies for those heartfelt moments.",
            "MOTIVATIONAL": "Powerful tracks to inspire and push you forward.",
            "INTENSE": "Strong, aggressive music to channel your energy and passion.",
            "FOCUSED": "Concentration-enhancing tracks for work or study sessions."
        }
        st.sidebar.markdown(f"*{mood_descriptions.get(st.session_state.mood, '')}*")
        st.sidebar.markdown("---")
        
        # Add refresh button in sidebar to get new recommendations for same mood
        if st.sidebar.button("Refresh Recommendations"):
            # Clear rejected tracks to allow for more variety
            st.session_state.rejected_tracks = set()
            
            # Get Spotify client
            sp = init_spotify()
            
            # Get new recommendations for current mood
            if sp:
                tracks = get_recommendations(sp, st.session_state.mood)
                if tracks:
                    st.session_state.tracks = tracks
                    st.rerun()
                else:
                    st.error("Sorry, couldn't get new recommendations at this time.")

    # Always define the columns before using them
    mood_col1, mood_col2 = st.columns([2, 1])
    
    with mood_col1:
        # Get user input for mood
        user_input = st.text_area("How are you feeling today?", height=100)
    
    with mood_col2:
        # Add a direct mood selection widget
        st.write("Or select a mood directly:")
        direct_mood = st.selectbox(
            "Choose mood", 
            ["Select...", "UPBEAT", "CALMING", "MELANCHOLY", "ROMANTIC", "MOTIVATIONAL", "INTENSE", "FOCUSED"],
            index=0,
            format_func=lambda x: x if x != "Select..." else "Select a mood..."
        )
    
    # Get recommendations button
    if st.button("Get Recommendations", type="primary"):
        if user_input or direct_mood != "Select...":
            with st.spinner("Analyzing your mood and finding tracks..."):
                # Determine mood - either from text input or direct selection
                if direct_mood != "Select...":
                    mood = direct_mood
                    mood_source = "direct selection"
                else:
                    mood = detect_mood(user_input)
                    mood_source = "text analysis"
                
                st.session_state.mood = mood
                st.session_state.mood_text = user_input  # Store the mood text for later reference
                
                # Get Spotify recommendations
                sp = init_spotify()
                if sp:
                    st.session_state.tracks = get_recommendations(sp, mood)
                    
                    # Clear rejected tracks when getting new recommendations for a new mood
                    st.session_state.rejected_tracks = set()
                    
                    # Show a success message with the detected mood
                    st.success(f"Found recommendations for {mood} mood (via {mood_source})")
                    
                    # Rerun to display the tracks
                    st.rerun()
        else:
            st.warning("Please enter how you're feeling or select a mood directly.")
    
    # Display tracks if available
    if st.session_state.tracks:
        st.write("Here are some songs for your mood:")
        
        # Get Spotify client for feedback actions
        sp = init_spotify()
        
        for idx, track in enumerate(st.session_state.tracks):
            # Create a unique key for each track
            track_key = f"track_{idx}_{track['id']}"
            
            # Create a container for each track
            with st.container():
                # Create columns for album art and track info
                img_col, info_col = st.columns([1, 3])
                
                # Display album art
                with img_col:
                    if track.get('album', {}).get('images') and len(track['album']['images']) > 0:
                        st.image(track['album']['images'][1]['url'] if len(track['album']['images']) > 1 else track['album']['images'][0]['url'], 
                                width=100)
                
                # Display track name, artist and album
                with info_col:
                    st.write(f"### {track['name']}")
                    st.write(f"**Artist:** {track['artists'][0]['name']}")
                    st.write(f"**Album:** {track['album']['name']}")
                    
                    # Get audio features to show why this track matches the mood
                    if st.button("Show Audio Features", key=f"features_{track_key}"):
                        try:
                            features = sp.audio_features(track['id'])[0]
                            if features:
                                # Create a radar chart or display key features
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**Energy:** {:.0%}".format(features['energy']))
                                    st.write("**Danceability:** {:.0%}".format(features['danceability']))
                                with col2:
                                    st.write("**Valence:** {:.0%}".format(features['valence']))
                                    st.write("**Acousticness:** {:.0%}".format(features['acousticness']))
                        except Exception as e:
                            st.error(f"Could not load audio features: {str(e)}")
                
                # Display embedded Spotify player with improved styling
                st.write(f"<iframe src=\"https://open.spotify.com/embed/track/{track['id']}\" width=\"100%\" height=\"80\" frameborder=\"0\" allowtransparency=\"true\" allow=\"encrypted-media; autoplay\"></iframe>", unsafe_allow_html=True)
                
                # Create feedback buttons with unique keys
                feedback_col1, feedback_col2, feedback_col3 = st.columns([1, 1, 1])
                with feedback_col1:
                    if st.button("👍 Like", key=f"like_{track_key}"):
                        # Add preference with current mood
                        current_mood = st.session_state.mood
                        if add_preference(current_mood, track['id'], track['name'], track['artists'][0]['name']):
                            st.success(f"Marked {track['name']} as a good match for {current_mood} mood!")
                            logger.info(f"Added preference for {track['name']} with mood {current_mood}")
                with feedback_col2:
                    if st.button("👎 Dislike", key=f"dislike_{track_key}"):
                        # Update preference with dislike using current mood
                        current_mood = st.session_state.mood
                        update_preference(current_mood, track['id'], 'dislike')
                        logger.info(f"Updated preference with dislike for {track['name']} with mood {current_mood}")
                        
                        # Add to general rejected tracks
                        st.session_state.rejected_tracks.add(track['id'])
                        
                        # Add to mood-specific disliked tracks with timestamp
                        add_mood_disliked_track(current_mood, track['id'])
                        st.info(f"Won't recommend this song for {current_mood} mood for a while")
                        
                        # Get a replacement track
                        if sp:
                            get_replacement_track(sp, idx, track)
                            
                with feedback_col3:
                    if st.button("⏭ Skip", key=f"skip_{track_key}"):
                        # Just add to rejected tracks without updating preference
                        st.session_state.rejected_tracks.add(track['id'])
                        
                        # Get a replacement track
                        if sp:
                            get_replacement_track(sp, idx, track)
                
                # Add some spacing
                st.write("---")

if __name__ == "__main__":
    main()