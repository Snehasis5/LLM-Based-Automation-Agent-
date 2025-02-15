# app/task_executor.py
import os
import subprocess
import re
import json
from datetime import datetime
import sqlite3
from typing import List, Tuple
import hashlib
import base64
import requests
import git
from bs4 import BeautifulSoup
from PIL import Image
import io
import csv
import tempfile

# Constants
DATA_DIR = "/data/"

def install_package(package: str):
    """Installs a package using uv."""
    try:
        subprocess.run(["uv", "pip", "install", package], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Package installation failed for {package}: {e.stderr}")

def run_datagen(user_email: str):
    """Runs datagen.py with the given user email."""
    datagen_url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"

    try:
        # Download datagen.py
        subprocess.run(["curl", "-o", os.path.join(DATA_DIR, "datagen.py"), datagen_url], check=True, capture_output=True, text=True)
        # Run datagen.py
        subprocess.run(["python", os.path.join(DATA_DIR, "datagen.py"), user_email], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"datagen.py execution failed: {e.stderr}")

def format_markdown(file_path: str, prettier_version: str = "3.4.2"):
    """Formats the markdown file using prettier."""
    try:
        # Check if prettier is installed. If not, install it
        try:
            subprocess.run(["prettier", "--version"], check=True, capture_output=True, text=True)
        except FileNotFoundError:
            install_package(f"prettier@{prettier_version}")  # Install if not found

        subprocess.run(["prettier", "--write", file_path], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Prettier formatting failed: {e.stderr}")

def count_wednesdays(file_path: str):
    """Counts the number of Wednesdays in the given file."""
    wednesday_count = 0
    try:
        with open(file_path, "r") as f:
            for line in f:
                try:
                    date_obj = datetime.strptime(line.strip(), "%Y-%m-%d")  # Adjust format if necessary
                    if date_obj.weekday() == 2:  # Wednesday is 2
                        wednesday_count += 1
                except ValueError:
                    print(f"Invalid date format: {line.strip()}") # Log the error, don't stop
        output_file = os.path.join(DATA_DIR, "dates-wednesdays.txt") # Hardcoded for now
        with open(output_file, "w") as outfile:
            outfile.write(str(wednesday_count))
    except FileNotFoundError:
        raise FileNotFoundError("dates.txt not found")

def sort_contacts(file_path: str):
    """Sorts the contacts in the JSON file by last_name, then first_name."""
    try:
        with open(file_path, 'r') as f:
            contacts = json.load(f)

        sorted_contacts = sorted(contacts, key=lambda x: (x['last_name'], x['first_name']))

        output_file = os.path.join(DATA_DIR, "contacts-sorted.json")
        with open(output_file, 'w') as outfile:
            json.dump(sorted_contacts, outfile, indent=4)

    except FileNotFoundError:
        raise FileNotFoundError("contacts.json not found")

def write_recent_logs(log_dir: str):
    """Writes the first line of the 10 most recent .log files to a file, most recent first."""
    try:
        log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
        log_files_with_paths = [os.path.join(log_dir, f) for f in log_files] # full path
        log_files_with_mtime = [(f, os.path.getmtime(f)) for f in log_files_with_paths]
        recent_logs = sorted(log_files_with_mtime, key=lambda x: x[1], reverse=True)[:10]

        output_lines = []
        for file_path, _ in recent_logs:
            try:
                with open(file_path, "r") as f:
                    first_line = f.readline().strip()
                    output_lines.append(first_line)
            except Exception as e:
                print(f"Error reading {file_path}: {e}") # log and continue

        output_file = os.path.join(DATA_DIR, "logs-recent.txt")
        with open(output_file, "w") as outfile:
            for line in output_lines:
                outfile.write(line + "\n")  # Most recent first

    except FileNotFoundError:
        raise FileNotFoundError("logs directory not found")

def create_markdown_index(docs_dir: str):
    """Creates an index file mapping markdown filenames to their first H1 heading."""
    index = {}
    for filename in os.listdir(docs_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(docs_dir, filename)
            try:
                with open(filepath, "r") as f:
                    for line in f:
                        if line.startswith("# "):
                            title = line[2:].strip()
                            index[filename] = title
                            break  # Only take the first H1
            except Exception as e:
                print(f"Error processing {filename}: {e}") # Log and continue

    output_file = os.path.join(DATA_DIR, "docs", "index.json")
    # Ensure the output dir exists:
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as outfile:
        json.dump(index, outfile, indent=4)

def extract_email_from_llm(email_file: str):
    """Extract email address from email message."""
    try:
        with open(email_file, "r") as f:
            email_content = f.read()
        prompt = f"""
        Extract the sender's email address from the following email:
        {email_content}
        Return ONLY the email address.
        """
        from agent import call_llm # avoid circular import
        email_address = call_llm(prompt).strip() # get email from LLM
        output_file = os.path.join(DATA_DIR, "email-sender.txt")
        with open(output_file, "w") as outfile:
            outfile.write(email_address)

    except FileNotFoundError:
        raise FileNotFoundError("email.txt not found")

def extract_credit_card_from_llm(image_file: str):
    """Extract credit card number from image using LLM."""
    try:
        install_package("Pillow") #Install pillow for image processing
        from PIL import Image
        image = Image.open(image_file)
        # Convert the image to base64
        import io
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        prompt = f"""
        Extract the credit card number from the following image in base64 format:
        {img_str}
        Return ONLY the credit card number without spaces.
        """

        from agent import call_llm
        card_number = call_llm(prompt).strip().replace(" ", "") # get card number from LLM
        output_file = os.path.join(DATA_DIR, "credit-card.txt")
        with open(output_file, "w") as outfile:
            outfile.write(card_number)

    except FileNotFoundError:
        raise FileNotFoundError("credit-card.png not found")

def find_similar_comments(comments_file: str):
    """Finds the most similar pair of comments using embeddings."""
    try:
        install_package("sentence-transformers")
        from sentence_transformers import SentenceTransformer, util

        with open(comments_file, "r") as f:
            comments = [line.strip() for line in f]

        model = SentenceTransformer('all-MiniLM-L6-v2')  # Or another suitable model
        embeddings = model.encode(comments, convert_to_tensor=True)

        # Compute cosine similarity between all pairs
        cosine_scores = util.cos_sim(embeddings, embeddings)

        # Find the pair with the highest similarity (excluding self-similarity)
        max_score = -1
        comment1_idx, comment2_idx = -1, -1

        for i in range(len(comments)):
            for j in range(i + 1, len(comments)):
                score = cosine_scores[i][j]
                if score > max_score:
                    max_score = score
                    comment1_idx, comment2_idx = i, j

        output_file = os.path.join(DATA_DIR, "comments-similar.txt")
        with open(output_file, "w") as outfile:
            outfile.write(comments[comment1_idx] + "\n")
            outfile.write(comments[comment2_idx] + "\n")

    except FileNotFoundError:
        raise FileNotFoundError("comments.txt not found")

def calculate_gold_ticket_sales(db_file: str):
    """Calculates the total sales of "Gold" tickets from the SQLite database."""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
        result = cursor.fetchone()[0]  # Get the sum

        conn.close()

        output_file = os.path.join(DATA_DIR, "ticket-sales-gold.txt")
        with open(output_file, "w") as outfile:
            outfile.write(str(result or 0))  # Write 0 if result is None

    except FileNotFoundError:
        raise FileNotFoundError("ticket-sales.db not found")
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

# Phase B Tasks
def fetch_data_from_api(api_url: str, output_file: str):
    """Fetches data from an API and saves it to a file."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        with open(output_file, "w") as f:
            f.write(response.text)
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {e}")

def clone_git_repo(repo_url: str, destination_dir: str):
    """Clones a Git repository to the specified directory."""
    try:
        git.Repo.clone_from(repo_url, destination_dir)
    except git.exc.GitCommandError as e:
        raise Exception(f"Git clone failed: {e}")

def run_sql_query(db_file: str, query: str, output_file: str):
    """Runs a SQL query on a SQLite database and saves the results to a file."""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        with open(output_file, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([col[0] for col in cursor.description])  # Write header
            writer.writerows(results)  # Write data

        conn.close()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def scrape_website(url: str, output_file: str):
    """Scrapes data from a website and saves it to a file."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text()  # Extract all text
        with open(output_file, "w") as f:
            f.write(text)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Web scraping failed: {e}")

def compress_resize_image(image_file: str, output_file: str, width: int = 200, height: int = 200):
    """Compresses or resizes an image and saves it to a file."""
    try:
        install_package("Pillow")  # Ensure Pillow is installed

        image = Image.open(image_file)
        image = image.resize((width, height))  # Resize
        image.save(output_file, optimize=True, quality=60)  # Compress and save

    except FileNotFoundError:
        raise FileNotFoundError("Image file not found")
    except Exception as e:
        raise Exception(f"Image processing failed: {e}")

def transcribe_audio(audio_file: str, output_file: str):
    """Transcribes audio from an MP3 file and saves the text to a file."""
    try:
        install_package("openai-whisper")
        import whisper
        model = whisper.load_model("tiny")  # Use a smaller model
        result = model.transcribe(audio_file)
        with open(output_file, "w") as f:
            f.write(result["text"])

    except Exception as e:
        raise Exception(f"Audio transcription failed: {e}")

def convert_markdown_to_html(markdown_file: str, output_file: str):
    """Converts Markdown to HTML and saves it to a file."""
    try:
        install_package("markdown")
        import markdown
        with open(markdown_file, "r") as f:
            markdown_text = f.read()
        html = markdown.markdown(markdown_text)
        with open(output_file, "w") as f:
            f.write(html)
    except FileNotFoundError:
        raise FileNotFoundError("Markdown file not found")
    except Exception as e:
        raise Exception(f"Markdown conversion failed: {e}")

def create_api_endpoint(csv_file: str, output_file: str):
    """Creates an API endpoint that filters a CSV file and returns JSON data (placeholder)."""
    print("Placeholder: Creating API endpoint...") # This is not fully implemented
    # This task is very complex and out of the scope for this project.
    # The "output_file" could contain instructions on how to create such an API.

    try:
      with open(csv_file, 'r') as file:
        csv_data = list(csv.reader(file))

      # Convert CSV data to JSON format
      json_data = json.dumps(csv_data, indent=4)

      # Write the JSON data to the output file
      with open(output_file, 'w') as file:
          file.write(json_data)

    except Exception as e:
        raise Exception(f"Unable to Create API Endpoint: {e}")