import os
import PyPDF2
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from config import (
    INPUT_DIR, OUTPUT_DIR, FLASHCARDS_DIR, THEMES_DIR, CACHE_DIR,
    MAX_FILE_SIZE_MB, MAX_ERRORS_PER_FILE, ERROR_COOLDOWN,
    MAX_PROCESSING_TIME, PAGES_PER_SECTION, MAX_SECTIONS
)
from model_handler import ModelHandler
from cache_handler import CacheHandler

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            
            # If file is large, process in sections
            if total_pages > 100:
                sections = []
                section_size = total_pages // 3  # Split into 3 sections
                
                for start in range(0, total_pages, section_size):
                    end = min(start + section_size, total_pages)
                    print(f"Processing pages {start+1} to {end}")
                    
                    section_text = ""
                    for i in range(start, end):
                        section_text += reader.pages[i].extract_text() + "\n"
                    sections.append(section_text)
                
                return sections
            else:
                # Process normally for smaller files
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return [text]
                
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {str(e)}")
        return None

async def process_pdf(filepath, model_handler):
    """Process a single PDF file."""
    filename = os.path.basename(filepath)
    clean_name = await model_handler.clean_filename(filename)
    print(f"\nProcessing: {clean_name}")
    
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(filepath)
        if not text:
            print(f"No text could be extracted from {filename}")
            return
        
        # Calculate total content size
        total_size = sum(len(section) for section in text)
        
        # Analyze themes
        themes = await analyze_themes(text, model_handler)
        if not themes:
            print(f"No themes found in {filename}")
            return
        
        # Calculate cards per theme based on content size
        # Aim for roughly 1 card per 1000 characters, minimum 5 per theme
        total_cards = max(total_size // 1000, len(themes) * 5)
        cards_per_theme = max(total_cards // len(themes), 5)
        print(f"Generating approximately {cards_per_theme} cards per theme ({len(themes)} themes)")
        
        # Generate flashcards for each theme
        all_flashcards = []
        for theme in themes:
            print(f"Generating cards for theme: {theme}")
            cards = await generate_flashcards_for_theme(theme, text, model_handler, count=cards_per_theme)
            all_flashcards.extend(cards)
        
        if not all_flashcards:
            print(f"No flashcards generated for {filename}")
            return
        
        # Save outputs
        save_outputs(clean_name, themes, all_flashcards)
        print(f"Successfully processed {filename}")
        print(f"Generated {len(all_flashcards)} flashcards across {len(themes)} themes")
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        raise

async def analyze_themes(text, model_handler):
    """Analyze themes in the text."""
    # If text is a list, join it with newlines
    if isinstance(text, list):
        text = "\n".join(text)
    
    prompt = """You are analyzing a medical textbook. Extract 5-10 key medical themes or topics.
    Return ONLY a JSON array of strings, no explanation or formatting.
    Each theme should be 2-5 words and describe a medical topic.
    
    Example good themes:
    ["Respiratory Physiology", "Gas Exchange", "Pulmonary Circulation", "Ventilation Mechanics"]
    
    Example bad themes (too generic/non-medical):
    ["Book Contents", "Digital Access", "Chapter Overview"]
    
    Text to analyze:
    """ + text[:2000]  # Using more text for better context
    
    # Create a stable hash for the text
    text_hash = str(hash(text[:2000].encode('utf-8')))
    cache_key = f"themes_{text_hash}"
    response = await model_handler.generate_response(prompt, cache_key=cache_key)
    
    try:
        # Clean up the response
        cleaned_response = response.strip()
        # Remove any markdown formatting
        if '```' in cleaned_response:
            parts = cleaned_response.split('```')
            if len(parts) >= 3:
                cleaned_response = parts[1]
                if cleaned_response.startswith('json'):
                    cleaned_response = cleaned_response[4:]
            else:
                cleaned_response = parts[-1]
        cleaned_response = cleaned_response.strip()
        
        # Extract JSON list from response
        themes = json.loads(cleaned_response)
        if not isinstance(themes, list):
            print("Invalid theme format - expected list")
            print(f"Raw response: {response}")
            return None
            
        # Filter out non-medical themes
        medical_themes = [theme for theme in themes if not any(x in theme.lower() for x in 
            ['ebook', 'digital', 'content', 'license', 'access', 'platform', 'account', 'support', 'chapter', 'contents'])]
        
        if not medical_themes:
            print("No medical themes found")
            print(f"Raw response: {response}")
            return None
            
        return medical_themes
        
    except json.JSONDecodeError:
        print("Failed to parse themes as JSON")
        print(f"Raw response: {response}")
        return None
    except Exception as e:
        print(f"Error analyzing themes: {str(e)}")
        print(f"Raw response: {response}")
        return None

async def generate_flashcards_for_theme(theme, text, model_handler, count=2):
    """Generate flashcards for a specific theme."""
    # If text is a list, join it with newlines
    if isinstance(text, list):
        text = "\n".join(text)
        
    prompt = f"""Create {count} medical multiple choice questions about {theme}.
    Return ONLY a JSON array where each question object has:
    - "question": the question text
    - "correct_answer": the correct answer (prefixed with A)
    - "wrong_answers": array of 3 wrong answers (prefixed with B,C,D)
    - "explanation": brief explanation of the correct answer
    
    Example output:
    [
      {{
        "question": "What is the primary function of alveoli?",
        "correct_answer": "A) Gas exchange between air and blood",
        "wrong_answers": [
          "B) Production of surfactant only",
          "C) Storage of oxygen",
          "D) Generation of negative pressure"
        ],
        "explanation": "Alveoli are specialized for gas exchange due to their thin walls and rich blood supply."
      }}
    ]
    
    Text to use:
    {text[:2000]}"""
    
    # Create a stable hash for the theme and text
    text_hash = str(hash(text[:2000].encode('utf-8')))
    theme_hash = str(hash(theme.encode('utf-8')))
    cache_key = f"cards_{theme_hash}_{text_hash}_{count}"
    response = await model_handler.generate_response(prompt, cache_key=cache_key)
    
    try:
        # Clean up the response
        cleaned_response = response.strip()
        if '```' in cleaned_response:
            parts = cleaned_response.split('```')
            if len(parts) >= 3:
                cleaned_response = parts[1]
                if cleaned_response.startswith('json'):
                    cleaned_response = cleaned_response[4:]
            else:
                cleaned_response = parts[-1]
        cleaned_response = cleaned_response.strip()
        
        # Remove any trailing commas before closing brackets (common JSON error)
        if cleaned_response.endswith(',]'):
            cleaned_response = cleaned_response[:-2] + ']'
        if cleaned_response.endswith(',}'):
            cleaned_response = cleaned_response[:-2] + '}'
        
        # Extract JSON list from response
        cards = json.loads(cleaned_response)
        if not isinstance(cards, list):
            print(f"Invalid flashcard format for theme {theme} - expected list")
            print(f"Raw response: {response}")
            return []
            
        # Validate each card
        valid_cards = []
        for card in cards:
            if all(k in card for k in ['question', 'correct_answer', 'wrong_answers', 'explanation']) and \
               isinstance(card['wrong_answers'], list) and len(card['wrong_answers']) == 3:
                valid_cards.append(card)
        
        if not valid_cards:
            print(f"No valid flashcards found for theme {theme}")
            print(f"Raw response: {response}")
            return []
            
        return valid_cards
        
    except json.JSONDecodeError:
        print(f"Failed to parse flashcards as JSON for theme {theme}")
        print(f"Raw response: {response}")
        return []
    except Exception as e:
        print(f"Error generating flashcards for theme {theme}: {str(e)}")
        print(f"Raw response: {response}")
        return []

def save_flashcards(book_id, flashcards):
    """Save flashcards to both JSON and readable format."""
    if not flashcards:
        return None, None
    
    # Save as JSON
    json_path = os.path.join(FLASHCARDS_DIR, f"{book_id}.json")
    with open(json_path, 'w') as f:
        json.dump(flashcards, f, indent=2)
    
    # Save in readable format
    txt_path = os.path.join(OUTPUT_DIR, "csv_output", f"{book_id}.txt")
    with open(txt_path, 'w') as f:
        f.write(f"Flashcards for: {book_id}\n")
        f.write("=" * 50 + "\n\n")
        
        for i, q in enumerate(flashcards, 1):
            f.write(f"Question {i}:\n")
            f.write(f"{q['question']}\n\n")
            f.write("Options:\n")
            # Combine all answers and sort by letter
            all_answers = [q['correct_answer']] + q['wrong_answers']
            all_answers.sort(key=lambda x: x[0])  # Sort by the letter prefix
            for ans in all_answers:
                f.write(f"{ans}\n")
            f.write(f"\nCorrect Answer: {q['correct_answer']}\n")
            if 'explanation' in q:
                f.write(f"\nExplanation: {q['explanation']}\n")
            f.write("\n" + "-"*50 + "\n\n")
    
    return json_path, txt_path

def save_outputs(clean_name, themes, flashcards):
    """Save themes and flashcards to files."""
    # Save themes
    theme_path = os.path.join(THEMES_DIR, f"{clean_name}_themes.json")
    with open(theme_path, 'w') as f:
        json.dump(themes, f, indent=2)
    
    # Save flashcards
    json_path, txt_path = save_flashcards(clean_name, flashcards)
    
    print(f"\nSaved outputs for {clean_name}:")
    print(f"- Themes: {theme_path}")
    print(f"- Flashcards (JSON): {json_path}")
    print(f"- Flashcards (Text): {txt_path}")

def ensure_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FLASHCARDS_DIR, exist_ok=True)
    os.makedirs(THEMES_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "csv_output"), exist_ok=True)

def get_pdf_files():
    """Get list of PDF files from input directory."""
    return [os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR) if f.endswith('.pdf')]

async def main():
    """Main function to process PDFs and generate flashcards."""
    load_dotenv()
    
    # Initialize the model handler
    gemini_key = os.getenv('GEMINI_API_KEY')
    mistral_key = os.getenv('MISTRAL_API_KEY')
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    if not mistral_key:
        raise ValueError("MISTRAL_API_KEY not found in environment")
    model_handler = ModelHandler(gemini_key, mistral_key, CACHE_DIR)
    
    # Create necessary directories
    ensure_directories()
    
    # Get list of PDF files
    pdf_files = get_pdf_files()
    if not pdf_files:
        print("No PDF files found in pdfInput directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF file
    for pdf_path in pdf_files:
        try:
            await process_pdf(pdf_path, model_handler)
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
            continue

async def generate_additional_flashcards(book_name: str, theme: str, count: int, model_handler: ModelHandler):
    """Generate additional flashcards for a specific theme."""
    # Load existing themes
    theme_path = os.path.join(THEMES_DIR, f"{book_name}_themes.json")
    if not os.path.exists(theme_path):
        print(f"No themes found for {book_name}")
        return None
        
    with open(theme_path, 'r') as f:
        themes = json.load(f)
    
    if theme not in themes:
        print(f"Theme '{theme}' not found in {book_name}")
        return None
    
    # Find the original PDF file
    pdf_files = get_pdf_files()
    pdf_path = None
    for path in pdf_files:
        clean_name = await model_handler.clean_filename(os.path.basename(path))
        if clean_name == book_name:
            pdf_path = path
            break
    
    if not pdf_path:
        print(f"Original PDF not found for {book_name}")
        return None
    
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"Could not extract text from {pdf_path}")
        return None
    
    # Generate new flashcards
    print(f"Generating {count} new flashcards for theme: {theme}")
    new_cards = await generate_flashcards_for_theme(theme, text, model_handler, count)
    
    if not new_cards:
        print("No new flashcards generated")
        return None
    
    # Load and update existing flashcards
    flashcards_path = os.path.join(FLASHCARDS_DIR, f"{book_name}.json")
    existing_cards = []
    if os.path.exists(flashcards_path):
        with open(flashcards_path, 'r') as f:
            existing_cards = json.load(f)
    
    # Add new cards
    existing_cards.extend(new_cards)
    
    # Save updated flashcards
    save_outputs(book_name, themes, existing_cards)
    print(f"Added {len(new_cards)} new flashcards for theme: {theme}")
    return new_cards

async def generate_random_flashcards(book_name: str, count: int, model_handler: ModelHandler):
    """Generate random flashcards across themes, weighted by content size."""
    # Load existing themes
    theme_path = os.path.join(THEMES_DIR, f"{book_name}_themes.json")
    if not os.path.exists(theme_path):
        print(f"No themes found for {book_name}")
        return None
        
    with open(theme_path, 'r') as f:
        themes = json.load(f)
    
    if not themes:
        print(f"No themes found in {book_name}")
        return None
    
    # Find the original PDF file
    pdf_files = get_pdf_files()
    pdf_path = None
    for path in pdf_files:
        clean_name = await model_handler.clean_filename(os.path.basename(path))
        if clean_name == book_name:
            pdf_path = path
            break
    
    if not pdf_path:
        print(f"Original PDF not found for {book_name}")
        return None
    
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"Could not extract text from {pdf_path}")
        return None
    
    # Join text sections
    full_text = "\n".join(text)
    
    # Calculate theme weights based on frequency in text
    theme_weights = {}
    for theme in themes:
        # Count occurrences of theme words in text (case insensitive)
        theme_words = theme.lower().split()
        weight = 1  # Base weight
        for word in theme_words:
            if len(word) > 3:  # Only count significant words
                weight += full_text.lower().count(word)
        theme_weights[theme] = max(weight, 1)  # Ensure minimum weight of 1
    
    # Calculate cards per theme based on weights
    total_weight = sum(theme_weights.values())
    cards_per_theme = {theme: max(int((weight / total_weight) * count), 1)
                      for theme, weight in theme_weights.items()}
    
    # Adjust to match requested count exactly
    while sum(cards_per_theme.values()) != count:
        if sum(cards_per_theme.values()) < count:
            # Add cards to themes with highest weights until we reach count
            sorted_themes = sorted(theme_weights.items(), key=lambda x: x[1], reverse=True)
            for theme, _ in sorted_themes:
                if sum(cards_per_theme.values()) >= count:
                    break
                cards_per_theme[theme] += 1
        else:
            # Remove cards from themes with lowest weights until we reach count
            sorted_themes = sorted(theme_weights.items(), key=lambda x: x[1])
            for theme, _ in sorted_themes:
                if sum(cards_per_theme.values()) <= count:
                    break
                if cards_per_theme[theme] > 1:
                    cards_per_theme[theme] -= 1
    
    # Generate flashcards for each theme
    print(f"\nGenerating {count} random flashcards for {book_name}:")
    all_new_cards = []
    for theme, theme_count in cards_per_theme.items():
        if theme_count > 0:
            print(f"Generating {theme_count} cards for theme: {theme}")
            cards = await generate_flashcards_for_theme(theme, text, model_handler, count=theme_count)
            if cards:
                all_new_cards.extend(cards)
    
    if not all_new_cards:
        print("No new flashcards generated")
        return None
    
    # Load and update existing flashcards
    flashcards_path = os.path.join(FLASHCARDS_DIR, f"{book_name}.json")
    existing_cards = []
    if os.path.exists(flashcards_path):
        with open(flashcards_path, 'r') as f:
            existing_cards = json.load(f)
    
    # Add new cards
    existing_cards.extend(all_new_cards)
    
    # Save updated flashcards
    save_outputs(book_name, themes, existing_cards)
    print(f"\nAdded {len(all_new_cards)} new flashcards across {len(cards_per_theme)} themes")
    for theme, theme_count in cards_per_theme.items():
        print(f"- {theme}: {theme_count} cards")
    return all_new_cards

async def generate_random_flashcards_all_books(count: int, model_handler: ModelHandler):
    """Generate random flashcards across all books and themes."""
    # Get all theme files
    theme_files = [f for f in os.listdir(THEMES_DIR) if f.endswith('_themes.json')]
    if not theme_files:
        print("No theme files found")
        return None
    
    # Load all themes and their books
    all_themes = {}  # {book_name: [themes]}
    for theme_file in theme_files:
        book_name = theme_file.replace('_themes.json', '')
        with open(os.path.join(THEMES_DIR, theme_file), 'r') as f:
            themes = json.load(f)
            if themes:
                all_themes[book_name] = themes
    
    if not all_themes:
        print("No themes found in any books")
        return None
    
    # Calculate total themes and cards per book
    total_themes = sum(len(themes) for themes in all_themes.values())
    cards_per_book = {book: max(int((len(themes) / total_themes) * count), 1)
                     for book, themes in all_themes.items()}
    
    # Adjust to match requested count exactly
    while sum(cards_per_book.values()) != count:
        if sum(cards_per_book.values()) < count:
            # Add cards to books with most themes
            sorted_books = sorted(all_themes.items(), key=lambda x: len(x[1]), reverse=True)
            for book, _ in sorted_books:
                if sum(cards_per_book.values()) >= count:
                    break
                cards_per_book[book] += 1
        else:
            # Remove cards from books with fewest themes
            sorted_books = sorted(all_themes.items(), key=lambda x: len(x[1]))
            for book, _ in sorted_books:
                if sum(cards_per_book.values()) <= count:
                    break
                if cards_per_book[book] > 1:
                    cards_per_book[book] -= 1
    
    # Generate flashcards for each book
    print(f"\nGenerating {count} random flashcards across all books:")
    all_new_cards = []
    for book_name, book_count in cards_per_book.items():
        if book_count > 0:
            print(f"\nGenerating {book_count} cards from {book_name}")
            cards = await generate_random_flashcards(book_name, book_count, model_handler)
            if cards:
                # Add book source to each card
                for card in cards:
                    card['source'] = book_name
                all_new_cards.extend(cards)
    
    if not all_new_cards:
        print("No flashcards generated")
        return None
    
    # Save to a special mixed cards file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mixed_cards_file = os.path.join(FLASHCARDS_DIR, f"mixed_cards_{timestamp}.json")
    with open(mixed_cards_file, 'w') as f:
        json.dump(all_new_cards, f, indent=2)
    
    # Save readable format
    txt_path = os.path.join(OUTPUT_DIR, "csv_output", f"mixed_cards_{timestamp}.txt")
    with open(txt_path, 'w') as f:
        f.write(f"Mixed Flashcards Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        
        for i, q in enumerate(all_new_cards, 1):
            f.write(f"Question {i} (from {q['source']}):\n")
            f.write(f"{q['question']}\n\n")
            f.write("Options:\n")
            # Combine all answers and sort by letter
            all_answers = [q['correct_answer']] + q['wrong_answers']
            all_answers.sort(key=lambda x: x[0])  # Sort by the letter prefix
            for ans in all_answers:
                f.write(f"{ans}\n")
            f.write(f"\nCorrect Answer: {q['correct_answer']}\n")
            if 'explanation' in q:
                f.write(f"\nExplanation: {q['explanation']}\n")
            f.write("\n" + "-"*50 + "\n\n")
    
    print(f"\nGenerated {len(all_new_cards)} flashcards across {len(cards_per_book)} books:")
    for book, book_count in cards_per_book.items():
        print(f"- {book}: {book_count} cards")
    print(f"\nSaved to:")
    print(f"- JSON: {mixed_cards_file}")
    print(f"- Text: {txt_path}")
    
    return all_new_cards

if __name__ == "__main__":
    asyncio.run(main()) 