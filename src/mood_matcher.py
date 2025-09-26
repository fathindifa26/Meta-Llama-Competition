import json
import logging
from typing import Dict, Optional, List
from openai import OpenAI

class MoodMatcher:
    def __init__(self, db):
        self.db = db
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key="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",
        )
        
    def create_ai_prompt(self, user_input: str) -> str:
        """Create AI prompt untuk mood-based recommendation."""
        menu_items = self.db.get_menu()
        
        # Build menu context for AI
        menu_context = ""
        for item in menu_items:
            mood_tags = item.get('mood_tags', '')
            menu_context += f"""
{item['name']} (ID: {item['id']}, Rp {item['price']:,}):
- Description: {item['description']}
- Mood Tags: {mood_tags}
"""
        
        prompt = f"""You are a coffee mood expert at a premium cafe. A customer said: "{user_input}"

Based on their mood/feeling, recommend the BEST coffee from our menu that matches their emotional state.

Our Menu:{menu_context}

Instructions:
1. Analyze their emotional state/mood from their input
2. Match it with the most suitable coffee based on mood tags and descriptions
3. Explain WHY this coffee matches their feeling in Indonesian language
4. Keep response warm, personal, and cafe-like
5. MUST respond in valid JSON format

Respond in this exact JSON format:
{{
    "recommended_item_id": [menu_id as integer],
    "confidence": [0-100 as integer],
    "reason": "Penjelasan personal mengapa kopi ini cocok dengan perasaanmu hari ini",
    "alternative": [alternative_menu_id as integer or null]
}}

Example matching logic:
- "tired/capek/butuh energi" → Americano (ID: 1) - focused, energetic
- "stressed/stress/lelah emosional" → Latte (ID: 3) - gentle, calm, nurturing
- "hot/panas/kepanasan" → Cold Brew (ID: 4) - cool, refreshing
- "cozy/nyaman/santai" → Cappuccino (ID: 2) - comfortable, cozy
- "creative/kreatif/mindful" → Matcha Latte (ID: 5) - zen, healthy, mindful"""
        
        return prompt

    def get_mood_recommendation(self, user_input: str) -> Dict:
        """Get mood-based recommendation dari LLM."""
        try:
            prompt = self.create_ai_prompt(user_input)
            
            completion = self.client.chat.completions.create(
                model="meta-llama/llama-3.3-8b-instruct:free",
                messages=[
                    {"role": "system", "content": "You are a professional coffee mood expert. Always respond in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,        # Slightly creative but consistent
                max_tokens=300,         # Reasonable length
                top_p=0.9,
                frequency_penalty=0.2,
                presence_penalty=0.1,
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Clean up response (remove markdown formatting if any)
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            # Parse JSON response
            try:
                recommendation = json.loads(response_text)
                
                # Validate response structure
                if not self._validate_recommendation(recommendation):
                    return self._fallback_recommendation(user_input)
                
                # Add menu item details
                menu_item = self._get_menu_item_by_id(recommendation['recommended_item_id'])
                if menu_item:
                    recommendation['menu_item'] = menu_item
                    
                    # Add alternative menu item if exists
                    if recommendation.get('alternative'):
                        alt_item = self._get_menu_item_by_id(recommendation['alternative'])
                        if alt_item:
                            recommendation['alternative_item'] = alt_item
                
                return {
                    'success': True,
                    'recommendation': recommendation
                }
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                print(f"Raw response: {response_text}")
                return self._fallback_recommendation(user_input)
                
        except Exception as e:
            print(f"❌ LLM API Error: {e}")
            return self._fallback_recommendation(user_input)
    
    def _validate_recommendation(self, rec: Dict) -> bool:
        """Validate recommendation structure."""
        required_fields = ['recommended_item_id', 'confidence', 'reason']
        
        if not all(field in rec for field in required_fields):
            return False
            
        if not isinstance(rec['recommended_item_id'], int):
            return False
            
        if not isinstance(rec['confidence'], int) or not (0 <= rec['confidence'] <= 100):
            return False
            
        if not isinstance(rec['reason'], str) or len(rec['reason'].strip()) < 10:
            return False
            
        return True
    
    def _get_menu_item_by_id(self, menu_id: int) -> Optional[Dict]:
        """Get menu item by ID."""
        menu_items = self.db.get_menu()
        for item in menu_items:
            if item['id'] == menu_id:
                return item
        return None
    
    def _fallback_recommendation(self, user_input: str) -> Dict:
        """Fallback recommendation jika LLM gagal."""
        # Simple keyword-based fallback
        user_lower = user_input.lower()
        
        fallback_map = {
            'tired|capek|energi|fokus|kerja': {'id': 1, 'reason': 'Americano cocok untuk memberikan energi dan fokus yang kamu butuhkan'},
            'stress|lelah|tenang|comfort': {'id': 3, 'reason': 'Latte memberikan rasa lembut dan menenangkan untuk meredakan stress'},
            'panas|hot|dingin|segar': {'id': 4, 'reason': 'Cold Brew perfect untuk cuaca panas dan memberikan kesegaran'},
            'nyaman|cozy|santai|hangout': {'id': 2, 'reason': 'Cappuccino memberikan kehangatan dan kenyamanan yang pas'},
            'kreatif|unik|sehat|mindful': {'id': 5, 'reason': 'Matcha Latte memberikan energi tenang yang cocok untuk aktivitas kreatif'}
        }
        
        for keywords, recommendation in fallback_map.items():
            if any(keyword in user_lower for keyword in keywords.split('|')):
                menu_item = self._get_menu_item_by_id(recommendation['id'])
                return {
                    'success': True,
                    'recommendation': {
                        'recommended_item_id': recommendation['id'],
                        'confidence': 75,
                        'reason': recommendation['reason'],
                        'alternative': None,
                        'menu_item': menu_item,
                        'is_fallback': True
                    }
                }
        
        # Ultimate fallback - most popular item
        popular = self.db.get_most_popular_item()
        if popular:
            return {
                'success': True,
                'recommendation': {
                    'recommended_item_id': popular['id'],
                    'confidence': 60,
                    'reason': f"{popular['name']} adalah pilihan populer yang cocok untuk berbagai suasana hati",
                    'alternative': None,
                    'menu_item': popular,
                    'is_fallback': True
                }
            }
        
        # Final fallback
        return {
            'success': False,
            'error': 'Tidak dapat memberikan rekomendasi saat ini'
        }

# Quick mood presets
MOOD_PRESETS = {
    'tired': 'Hari ini capek banget, butuh yang bikin semangat tapi gak terlalu strong',
    'stress': 'Lagi stress dan butuh sesuatu yang menenangkan jiwa',
    'hot': 'Cuaca panas banget hari ini, pengen yang seger dan dingin',
    'focus': 'Butuh konsentrasi tinggi untuk kerja, cariin yang bikin fokus',
    'cozy': 'Pengen suasana nyaman dan hangat buat santai-santai',
    'creative': 'Lagi mood kreatif dan pengen sesuatu yang unik'
}

def get_mood_preset(mood_key: str) -> str:
    """Get predefined mood text."""
    return MOOD_PRESETS.get(mood_key, mood_key)