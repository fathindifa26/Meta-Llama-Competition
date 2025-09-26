from flask import Blueprint, request, jsonify
from .mood_matcher import MoodMatcher, get_mood_preset

def create_mood_api(db):
    """Create mood-based recommendation API blueprint."""
    mood_bp = Blueprint('mood', __name__)
    mood_matcher = MoodMatcher(db)
    
    @mood_bp.route('/api/mood-recommendation', methods=['POST'])
    def get_mood_recommendation():
        """Get mood-based menu recommendation."""
        try:
            data = request.get_json()
            
            if not data or 'user_input' not in data:
                return jsonify({
                    'success': False,
                    'error': 'user_input is required'
                }), 400
            
            user_input = data['user_input'].strip()
            
            if not user_input:
                return jsonify({
                    'success': False,
                    'error': 'user_input cannot be empty'
                }), 400
            
            # Get recommendation from LLM
            result = mood_matcher.get_mood_recommendation(user_input)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
    
    @mood_bp.route('/api/mood-presets', methods=['GET'])
    def get_mood_presets():
        """Get predefined mood presets."""
        from .mood_matcher import MOOD_PRESETS
        return jsonify({
            'success': True,
            'presets': MOOD_PRESETS
        })
    
    @mood_bp.route('/api/mood-recommendation/preset/<mood_key>', methods=['POST'])
    def get_preset_recommendation(mood_key):
        """Get recommendation for predefined mood."""
        try:
            preset_text = get_mood_preset(mood_key)
            
            if preset_text == mood_key:  # Not found
                return jsonify({
                    'success': False,
                    'error': 'Mood preset not found'
                }), 404
            
            # Get recommendation using preset
            result = mood_matcher.get_mood_recommendation(preset_text)
            
            # Add preset info
            if result['success']:
                result['preset_used'] = {
                    'key': mood_key,
                    'text': preset_text
                }
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500
    
    return mood_bp