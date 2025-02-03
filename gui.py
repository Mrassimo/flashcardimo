import os
import json
import asyncio
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dotenv import load_dotenv
from model_handler import ModelHandler
from main import (
    process_pdf, generate_additional_flashcards,
    generate_random_flashcards, generate_random_flashcards_all_books,
    THEMES_DIR, CACHE_DIR
)

class FlashcardGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Medical Flashcard Generator")
        self.root.geometry("800x600")
        
        # Initialize model handler
        load_dotenv()
        gemini_key = os.getenv('GEMINI_API_KEY')
        mistral_key = os.getenv('MISTRAL_API_KEY')
        if not gemini_key or not mistral_key:
            messagebox.showerror("Error", "API keys not found. Please check your .env file.")
            root.destroy()
            return
        
        self.model_handler = ModelHandler(gemini_key, mistral_key, CACHE_DIR)
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs
        self.process_tab = ttk.Frame(self.notebook)
        self.generate_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.process_tab, text='Process PDFs')
        self.notebook.add(self.generate_tab, text='Generate Cards')
        
        self._setup_process_tab()
        self._setup_generate_tab()
        
        # Progress bar and status
        self.status_frame = ttk.Frame(root)
        self.status_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side='left')
        
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.pack(side='right', fill='x', expand=True, padx=(10, 0))
    
    def _setup_process_tab(self):
        # PDF List
        list_frame = ttk.LabelFrame(self.process_tab, text="PDF Files")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.pdf_list = tk.Listbox(list_frame, selectmode='extended')
        self.pdf_list.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.pdf_list.yview)
        scrollbar.pack(side='right', fill='y')
        self.pdf_list.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        btn_frame = ttk.Frame(self.process_tab)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Add PDFs", command=self.add_pdfs).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_pdfs).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Process Selected", command=self.process_pdfs).pack(side='right', padx=5)
    
    def _setup_generate_tab(self):
        # Book selection
        book_frame = ttk.LabelFrame(self.generate_tab, text="Select Book")
        book_frame.pack(fill='x', padx=10, pady=5)
        
        self.book_var = tk.StringVar(value="All Books")
        self.book_combo = ttk.Combobox(book_frame, textvariable=self.book_var)
        self.book_combo.pack(fill='x', padx=5, pady=5)
        self.book_combo.bind('<<ComboboxSelected>>', self.update_themes)
        
        # Theme selection
        theme_frame = ttk.LabelFrame(self.generate_tab, text="Select Theme")
        theme_frame.pack(fill='x', padx=10, pady=5)
        
        self.theme_var = tk.StringVar(value="Random")
        self.theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var)
        self.theme_combo.pack(fill='x', padx=5, pady=5)
        
        # Number of cards
        num_frame = ttk.LabelFrame(self.generate_tab, text="Number of Cards")
        num_frame.pack(fill='x', padx=10, pady=5)
        
        self.num_cards = ttk.Spinbox(num_frame, from_=1, to=100, increment=1)
        self.num_cards.set(10)
        self.num_cards.pack(fill='x', padx=5, pady=5)
        
        # Generate button
        ttk.Button(self.generate_tab, text="Generate Cards", 
                  command=self.generate_cards).pack(pady=20)
        
        self.update_books()
    
    def update_books(self):
        """Update the list of available books."""
        theme_files = [f for f in os.listdir(THEMES_DIR) if f.endswith('_themes.json')]
        books = ["All Books"] + [f.replace('_themes.json', '') for f in theme_files]
        self.book_combo['values'] = books
        self.book_var.set("All Books")
        self.update_themes()
    
    def update_themes(self, event=None):
        """Update the list of available themes for the selected book."""
        book = self.book_var.get()
        if book == "All Books":
            self.theme_combo['values'] = ["Random"]
            self.theme_var.set("Random")
            self.theme_combo.configure(state='disabled')
        else:
            theme_file = os.path.join(THEMES_DIR, f"{book}_themes.json")
            if os.path.exists(theme_file):
                with open(theme_file, 'r') as f:
                    themes = json.load(f)
                self.theme_combo['values'] = ["Random"] + themes
                self.theme_var.set("Random")
                self.theme_combo.configure(state='normal')
    
    def add_pdfs(self):
        """Add PDFs to the list."""
        files = filedialog.askopenfilenames(
            title="Select PDFs",
            filetypes=[("PDF files", "*.pdf")]
        )
        for file in files:
            self.pdf_list.insert('end', file)
    
    def remove_pdfs(self):
        """Remove selected PDFs from the list."""
        selection = self.pdf_list.curselection()
        for index in reversed(selection):
            self.pdf_list.delete(index)
    
    async def process_single_pdf(self, filepath):
        """Process a single PDF file."""
        try:
            await process_pdf(filepath, self.model_handler)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error processing {os.path.basename(filepath)}: {str(e)}")
            return False
    
    def process_pdfs(self):
        """Process selected PDF files."""
        selection = self.pdf_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select PDFs to process")
            return
        
        self.progress.start()
        self.status_label.configure(text="Processing PDFs...")
        
        async def process_all():
            for index in selection:
                filepath = self.pdf_list.get(index)
                await self.process_single_pdf(filepath)
            self.progress.stop()
            self.status_label.configure(text="Ready")
            self.update_books()
            messagebox.showinfo("Success", "PDF processing complete!")
        
        asyncio.run(process_all())
    
    def generate_cards(self):
        """Generate flashcards based on current settings."""
        try:
            count = int(self.num_cards.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of cards")
            return
        
        self.progress.start()
        self.status_label.configure(text="Generating flashcards...")
        
        async def generate():
            book = self.book_var.get()
            theme = self.theme_var.get()
            
            try:
                if book == "All Books":
                    await generate_random_flashcards_all_books(count, self.model_handler)
                elif theme == "Random":
                    await generate_random_flashcards(book, count, self.model_handler)
                else:
                    await generate_additional_flashcards(book, theme, count, self.model_handler)
                
                self.progress.stop()
                self.status_label.configure(text="Ready")
                messagebox.showinfo("Success", "Flashcards generated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Error generating flashcards: {str(e)}")
                self.progress.stop()
                self.status_label.configure(text="Ready")
        
        asyncio.run(generate())

def main():
    root = tk.Tk()
    app = FlashcardGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 