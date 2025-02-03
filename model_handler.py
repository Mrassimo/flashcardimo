import json
import os
import time
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import google.generativeai as genai
from cache_handler import CacheHandler

class ModelHandler:
    GEMINI_MODEL = 'gemini-2.0-flash-exp'
    MISTRAL_MODEL = 'mistral-small-latest'
    
    def __init__(self, gemini_api_key: str, mistral_api_key: str, cache_dir: str):
        self.gemini_model = genai.GenerativeModel(self.GEMINI_MODEL)
        self.mistral_client = MistralClient(api_key=mistral_api_key)
        self.cache_handler = CacheHandler(cache_dir)
        genai.configure(api_key=gemini_api_key)
        self.current_model = "gemini"
        self.consecutive_errors = 0
        self.error_threshold = 3
        self.cooldown_start = 0
        self.cooldown_period = 60  # 1 minute cooldown
    
    def _should_switch_model(self):
        """Determine if we should switch models based on errors and cooldown."""
        if self.consecutive_errors >= self.error_threshold:
            if time.time() - self.cooldown_start >= self.cooldown_period:
                self.consecutive_errors = 0
                return True
        return False
    
    def _format_prompt(self, prompt):
        """Format prompt based on current model."""
        if self.current_model == "gemini":
            return prompt
        else:  # Mistral needs a system prompt
            return prompt  # System prompt is handled in the API call
    
    async def generate_response(self, prompt, cache_key=None):
        """Generate response using current model with fallback."""
        if cache_key:
            cached = self.cache_handler.get(cache_key)
            if cached:
                return cached
        
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                if self._should_switch_model():
                    self.current_model = "gemini" if self.current_model == "mistral" else "mistral"
                    print(f"Switching to {self.current_model} model")
                
                formatted_prompt = self._format_prompt(prompt)
                
                if self.current_model == "gemini":
                    try:
                        response = self.gemini_model.generate_content(formatted_prompt)
                        result = response.text
                    except Exception as e:
                        if "429" in str(e):  # Quota exceeded
                            print(f"Gemini quota exceeded, switching to Mistral...")
                            self.current_model = "mistral"
                            continue
                        raise
                else:  # Mistral
                    try:
                        messages = [
                            ChatMessage(role="system", content="You are a medical education expert specialized in creating clear, accurate multiple choice questions."),
                            ChatMessage(role="user", content=prompt)
                        ]
                        response = self.mistral_client.chat(
                            model=self.MISTRAL_MODEL,
                            messages=messages
                        )
                        result = response.choices[0].message.content
                    except Exception as e:
                        if "429" in str(e):  # Quota exceeded
                            print(f"Mistral quota exceeded, switching to Gemini...")
                            self.current_model = "gemini"
                            continue
                        raise
                
                self.consecutive_errors = 0  # Reset error count on success
                if cache_key:
                    self.cache_handler.set(cache_key, result)
                return result
                
            except Exception as e:
                print(f"Error with {self.current_model}: {str(e)}")
                self.consecutive_errors += 1
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Waiting 30s before retry {retry_count + 1}...")
                    time.sleep(30)
                continue
        
        raise Exception(f"Failed to generate response after {max_retries} retries with both models")

    async def clean_filename(self, filename: str) -> str:
        prompt = f"""Given this filename: "{filename}", extract just the book title and year.
        Return ONLY a JSON object with 'title' and 'year' fields.
        Rules:
        1. Keep possessive names in official titles (e.g., "Guyton's", "Ganong's", "Vander's")
        2. Keep descriptive medical terms (e.g., "Clinical", "Applied", "Basic")
        3. Keep "and" if part of subject or brand (e.g., "Anatomy and Physiology", "Nunn and Lumb's")
        
        Example: For "Basic Physics and Measurement in Anaesthesia-Butterworth-Heinemann (1995).pdf"
        Return: {{"title": "Basic Physics and Measurement in Anaesthesia", "year": "1995"}}"""
        
        try:
            response = await self.generate_response(prompt, cache_key=f"filename_{hash(filename)}")
            # Clean up markdown formatting
            if '```' in response:
                parts = response.split('```')
                if len(parts) >= 3:
                    response = parts[1]
                    if response.startswith('json'):
                        response = response[4:]
                else:
                    response = parts[-1]
            response = response.strip()
            
            data = json.loads(response)
            title = data['title'].replace(' ', '_')
            return f"{title}_{data['year']}" if data.get('year') else title
        except Exception as e:
            print(f"Error cleaning filename with AI: {str(e)}")
            print(f"Raw response: {response if 'response' in locals() else 'No response'}")
            return os.path.splitext(filename)[0].split('--')[0].strip().replace(' ', '_') 