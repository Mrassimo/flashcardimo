# Medical Flashcard Generator

A sophisticated tool for generating high-quality medical MCQs from textbooks, specifically designed for Intensive Care and Anesthesia primary exam preparation.

## Features

- 🔍 Intelligent text analysis and theme extraction
- 📚 Processes multiple medical textbooks
- 🎯 Generates exam-style MCQs with clinical scenarios
- 📊 Creates a comprehensive syllabus
- 💾 Smart caching and progress tracking
- 🔄 Resume capability for long processing tasks
- 🎨 Simple GUI interface for easy use

## Quick Start

### For Mac Users
1. Download and unzip the application
2. Double-click `install_mac.command`
3. When prompted, enter your password for Homebrew installation
4. Add your API keys to the `.env` file when it opens
5. Double-click `start_mac.command` to launch the application

### For Windows Users
1. Download and unzip the application
2. Double-click `install_windows.bat`
3. Follow the installation prompts
4. Add your API keys to the `.env` file when it opens
5. Double-click `start_windows.bat` to launch the application

## Prerequisites

You'll need API keys from:
- [Google AI Studio](https://makersuite.google.com/app/apikey) (Gemini API)
- [Mistral Platform](https://console.mistral.ai/) (Mistral API)

The installation scripts will automatically install all other requirements, including Python if needed.

## Using the Application

1. **Process PDFs Tab:**
   - Click "Add PDFs" to select your medical textbooks
   - Select the PDFs you want to process
   - Click "Process Selected" to start analysis

2. **Generate Cards Tab:**
   - Choose "All Books" or a specific book
   - Select "Random" or a specific theme
   - Set the number of cards you want
   - Click "Generate Cards"

## Directory Structure

```
FlashCardGens/
├── pdfInput/           # Place your PDFs here
├── Outputs/
│   ├── cache/         # API response cache
│   ├── csv_output/    # Human-readable flashcards
│   ├── flashcards/    # JSON flashcards
│   └── themes/        # Extracted themes
├── install_mac.command    # Mac installer
├── start_mac.command      # Mac launcher
├── install_windows.bat    # Windows installer
├── start_windows.bat      # Windows launcher
└── requirements.txt       # Dependencies
```

## Generated Output

### Flashcard Format
Each flashcard includes:
- Question text
- 4 multiple choice options (A, B, C, D)
- Correct answer
- Detailed explanation
- Source book reference

### File Formats
- JSON files for programmatic use
- Text files for easy reading
- Mixed sets with cards from multiple books

## Troubleshooting

If you encounter any issues:
1. Make sure your API keys are correctly added to the `.env` file
2. Check that your PDFs are readable and not password-protected
3. Ensure you have an active internet connection
4. Try running the installation script again

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 