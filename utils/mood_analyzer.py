import torch
from transformers import pipeline
import logging

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

def get_mood_analyzer():
    try:
        logger.info("Initializing mood analyzer...")
        device = "cpu"  # Force CPU to avoid CUDA issues
        
        # Try to load the model with a timeout
        try:
            analyzer = pipeline(
                "text-classification", 
                model="finiteautomata/bertweet-base-sentiment-analysis",
                device=-1  # -1 means CPU
            )
            logger.info("Mood analyzer initialized successfully")
            return analyzer
        except Exception as model_error:
            logger.error(f"Error loading sentiment model: {str(model_error)}")
            logger.info("Using keyword-only mood detection as fallback")
            return None
    except Exception as e:
        logger.error(f"Error initializing mood analyzer: {str(e)}")
        return None

mood_analyzer = get_mood_analyzer()

def get_mood_category(sentiment):
    if sentiment == 'POSITIVE':
        return 'UPBEAT'
    elif sentiment == 'NEGATIVE':
        return 'CALMING'
    else:  # NEUTRAL
        return 'MOTIVATIONAL'

def detect_mood(text):
    try:
        # Map text to mood based on emotional content
        text_lower = text.lower()
        
        # Define keyword groups with stronger matching for expanded moods
        mood_keywords = {
            "UPBEAT": ['happy', 'joy', 'excited', 'upbeat', 'cheerful', 'fun', 'energetic', 
                      'party', 'dance', 'celebrate', 'positive', 'great', 'awesome', 
                      'amazing', 'good', 'wonderful', 'fantastic', 'excellent', 'thrilled',
                      'delighted', 'ecstatic', 'enthusiastic', 'lively', 'vibrant'],
            
            "CALMING": ['relax', 'calm', 'peaceful', 'quiet', 'chill', 'mellow', 'gentle', 
                      'soothing', 'tired', 'sleepy', 'tranquil', 'serene', 'rest', 
                      'meditate', 'unwind', 'breathe', 'comfort', 'ease', 'harmony'],
            
            "MELANCHOLY": ['sad', 'depressed', 'down', 'blue', 'unhappy', 'lonely', 'missing',
                         'heartbreak', 'tears', 'cry', 'grief', 'sorrow', 'regret', 'nostalgia',
                         'wistful', 'yearning', 'longing', 'hurt', 'pain', 'emotional'],
            
            "ROMANTIC": ['love', 'heart', 'romantic', 'passion', 'desire', 'affection',
                       'intimate', 'tender', 'sweet', 'adore', 'cherish', 'embrace',
                       'relationship', 'together', 'couple', 'date', 'kiss'],
            
            "MOTIVATIONAL": ['motivated', 'inspired', 'determined', 'focused', 'energized', 
                           'strong', 'power', 'achieve', 'success', 'goal', 'win', 
                           'challenge', 'overcome', 'push', 'drive', 'ambition', 'hustle',
                           'grind', 'discipline', 'persistence', 'dedication'],
            
            "INTENSE": ['angry', 'rage', 'fury', 'intense', 'aggressive', 'powerful', 
                      'fierce', 'wild', 'rebel', 'fight', 'battle', 'strength', 'force',
                      'heavy', 'dark', 'deep', 'raw', 'primal', 'unstoppable'],
            
            "FOCUSED": ['study', 'work', 'concentrate', 'focus', 'productive', 'efficient',
                      'learn', 'think', 'create', 'build', 'develop', 'progress', 'improve',
                      'grow', 'analyze', 'solve', 'research', 'code', 'write', 'read']
        }
        
        # Count keyword matches in each category
        mood_scores = {}
        for mood, keywords in mood_keywords.items():
            mood_scores[mood] = sum(1 for word in keywords if word in text_lower)
        
        logger.info(f"Keyword matches: {mood_scores}")
        
        # If we have keyword matches, use the category with the most matches
        max_score = max(mood_scores.values()) if mood_scores else 0
        if max_score > 0:
            # Get all moods with the max score
            top_moods = [mood for mood, score in mood_scores.items() if score == max_score]
            if len(top_moods) == 1:
                return top_moods[0]
        
        # If no clear winner from keywords or tied, try sentiment analysis if available
        if mood_analyzer is not None:
            try:
                result = mood_analyzer(text)[0]
                # Map sentiment to mood
                if result['label'] == 'POSITIVE':
                    # For positive sentiment, check if it's more energetic or calm
                    if any(word in text_lower for word in ['energetic', 'excited', 'happy', 'fun']):
                        return "UPBEAT"
                    elif any(word in text_lower for word in ['love', 'heart', 'sweet']):
                        return "ROMANTIC"
                    else:
                        return "UPBEAT"
                elif result['label'] == 'NEGATIVE':
                    # For negative sentiment, check if it's sad or angry
                    if any(word in text_lower for word in ['angry', 'mad', 'rage', 'hate']):
                        return "INTENSE"
                    else:
                        return "MELANCHOLY"
                else:  # Neutral
                    # For neutral, check if it's focused or motivational
                    if any(word in text_lower for word in ['work', 'study', 'focus']):
                        return "FOCUSED"
                    else:
                        return "MOTIVATIONAL"
            except Exception as sentiment_error:
                logger.error(f"Error in sentiment analysis: {str(sentiment_error)}")
                # Continue to fallback
        
        # Use text content analysis as a fallback
        question_words = ['how', 'what', 'why', 'when', 'where', 'who']
        if any(text_lower.startswith(word) for word in question_words) or '?' in text:
            return "FOCUSED"  # Questions often indicate a focused state
        
        # Check for exclamation marks or all caps (excitement or intensity)
        if '!' in text or text.isupper():
            return "UPBEAT" if any(word in text_lower for word in ['love', 'happy', 'great']) else "INTENSE"
        
        # If still no match, use text length as a heuristic
        if len(text) < 15:
            return "UPBEAT"  # Short texts tend to be more direct/energetic
        elif len(text) > 40:
            return "CALMING"  # Longer texts tend to be more reflective
        else:
            return "MOTIVATIONAL"  # Default for medium-length text
            
    except Exception as e:
        logger.error(f"Error detecting mood: {str(e)}")
        return "MOTIVATIONAL"  # Default fallback mood