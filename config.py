import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directory Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.getenv('PDF_INPUT_DIR', 'pdfInput')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'Outputs')
FLASHCARDS_DIR = os.path.join(OUTPUT_DIR, 'flashcards')
THEMES_DIR = os.path.join(OUTPUT_DIR, 'themes')
CACHE_DIR = os.path.join(OUTPUT_DIR, 'cache')
CSV_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "csv_output")

# Create all necessary directories
for directory in [INPUT_DIR, OUTPUT_DIR, FLASHCARDS_DIR, THEMES_DIR, CACHE_DIR, CSV_OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)

# PDF Processing Configuration
MAX_FILE_SIZE_MB = 50  # Maximum file size to process at once
PAGES_PER_SECTION = 100  # Number of pages to process at once
MAX_SECTIONS = 10  # Maximum number of sections to process
SECTION_OVERLAP = 5  # Number of pages to overlap between sections

# Error Handling
MAX_ERRORS_PER_FILE = 3  # Maximum errors before skipping file
ERROR_COOLDOWN = 90  # Seconds to wait after error
MAX_PROCESSING_TIME = 7200  # 2 hours maximum processing time per file

# Cache Configuration
CACHE_EXPIRY = 24 * 60 * 60  # 24 hours cache expiry

# API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_RATE_LIMIT = int(os.getenv('GEMINI_RATE_LIMIT', '25'))  # Maximum requests per minute
GEMINI_RETRY_DELAY = int(os.getenv('GEMINI_RETRY_DELAY', '70'))  # Seconds to wait when rate limited

# Content Processing
MAX_CHUNK_SIZE = 600  # Characters per chunk for API calls
MIN_CHUNK_SIZE = 200  # Minimum chunk size for API calls
BATCH_SIZE = 2  # Number of chunks to process at once
CARDS_PER_CHUNK = 2  # Number of flashcards to generate per chunk

# Theme Configuration
MIN_THEME_SIMILARITY = 0.2  # Minimum similarity for theme matching
MAX_THEMES = 15            # Maximum number of themes per section
MIN_THEME_LENGTH = 5       # Minimum characters in a theme
MAX_THEME_LENGTH = 100     # Maximum characters in a theme

# Error Handling
ERROR_COOLDOWN = 90        # Seconds to wait after error
MAX_PROCESSING_TIME = 7200  # Increased to 2 hours for large files

# Cache Configuration
CACHE_EXPIRY = 7 * 24 * 60 * 60  # Cache entries expire after 7 days

# File Structure Configuration
EXTRACTED_CONTENT_DIR = os.path.join(OUTPUT_DIR, "extracted_content")
TEXTS_DIR = os.path.join(EXTRACTED_CONTENT_DIR, "texts")
TOCS_DIR = os.path.join(EXTRACTED_CONTENT_DIR, "tocs")
PROCESSED_TOCS_DIR = os.path.join(TOCS_DIR, "processed")

# Create directories if they don't exist
for directory in [EXTRACTED_CONTENT_DIR, TEXTS_DIR, TOCS_DIR, PROCESSED_TOCS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Processing Configuration
MAX_CHUNK_SIZE = 600    # Reduced for more focused content
MIN_CHUNK_SIZE = 200    # Reduced to allow more granular chunks
BATCH_SIZE = 2         # Reduced to minimize API rate limit issues
MAX_RETRIES = 5        # Keep retries at 5
MAX_FILE_SIZE_MB = 50  # Maximum file size to process at once

# Flashcard Generation Configuration
CARDS_PER_CHUNK = 2     # Keep at 2 for quality
MIN_THEME_SIMILARITY = 0.2  # Increased for better matching

# Cache Configuration
USE_CACHE = True
CACHE_EXPIRY = 24 * 60 * 60  # 24 hours

# Theme Analysis Configuration
MAX_THEMES = 15        # Increased slightly for better coverage
MIN_THEME_LENGTH = 10  # Keep minimum length
MAX_THEME_LENGTH = 80  # Reduced maximum length for cleaner themes
MIN_THEME_WORDS = 2    # Minimum words in a theme
MAX_THEME_WORDS = 6    # Maximum words in a theme
MIN_CONTENT_WORDS = 20 # Minimum words in section content

# Content Validation Configuration
MIN_SECTION_SIMILARITY = 0.5  # Minimum similarity between header and content
MAX_PROPER_NOUN_RATIO = 0.8  # Maximum ratio of proper nouns in theme
MIN_MEANINGFUL_WORDS = 1     # Minimum meaningful words in theme

# Performance Configuration
CHUNK_OVERLAP = 50          # Words to overlap between chunks
SAVE_INTERVAL = 5           # Save progress every N successful chunks
PROGRESS_UPDATE = 10        # Print progress every N chunks
MAX_CACHE_SIZE_MB = 100     # Maximum cache size in MB 