# app/agent.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

#import os
import json
import subprocess
import requests

# Constants
DATA_DIR = "/data/"
AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")

LLM_MODEL = "gpt-4o-mini" # Enforce model use.

# Import Task Executor Functions
from task_executor import (
    install_package,
    run_datagen,
    format_markdown,
    count_wednesdays,
    sort_contacts,
    write_recent_logs,
    create_markdown_index,
    extract_email_from_llm,
    extract_credit_card_from_llm,
    find_similar_comments,
    calculate_gold_ticket_sales,
    # Phase B functions:
    fetch_data_from_api,
    clone_git_repo,
    run_sql_query,
    scrape_website,
    compress_resize_image,
    transcribe_audio,
    convert_markdown_to_html,
    create_api_endpoint,
)


def call_llm(prompt: str) -> str:
    """Calls the LLM with the given prompt and returns the response."""
    if not AIPROXY_TOKEN:
        raise ValueError("AIPROXY_TOKEN environment variable not set.")

    url = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"  # Replace with the actual AI Proxy URL
    headers = {
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)  # Set a reasonable timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()["result"]  # Assuming the response structure
    except requests.exceptions.RequestException as e:
        raise Exception(f"LLM API Error: {e}")


async def run_task(task_description: str):
    """
    Main function to orchestrate task execution. Parses the task description
    and calls the appropriate functions.
    """
    prompt = f"""
    You are an autonomous agent designed to parse task descriptions and generate a JSON-formatted instruction set to perform the task.
    The environment is a sandboxed Linux environment. You have access to standard shell commands and specific pre-installed tools.
    Follow the instructions precisely.

    You have access to the following functions.  Use them as needed:
    - install_package(package_name: str)
    - run_datagen(user_email: str)
    - format_markdown(file_path: str, prettier_version: str = "3.4.2")
    - count_wednesdays(file_path: str)
    - sort_contacts(file_path: str)
    - write_recent_logs(log_dir: str)
    - create_markdown_index(docs_dir: str)
    - extract_email_from_llm(email_file: str)
    - extract_credit_card_from_llm(image_file: str)
    - find_similar_comments(comments_file: str)
    - calculate_gold_ticket_sales(db_file: str)
    - fetch_data_from_api(api_url: str, output_file: str)
    - clone_git_repo(repo_url: str, destination_dir: str)
    - run_sql_query(db_file: str, query: str, output_file: str)
    - scrape_website(url: str, output_file: str)
    - compress_resize_image(image_file: str, output_file: str)
    - transcribe_audio(audio_file: str, output_file: str)
    - convert_markdown_to_html(markdown_file: str, output_file: str)
    - create_api_endpoint(csv_file: str, output_file: str)

    Here are some known useful shell tools and their usages:

    - `uv`: A fast package installer and resolver for Python.  Use to install packages such as prettifier.
    - `prettier`: A code formatter. Run like so: `prettier --write <file_path>`
    - `python`: A python interpretter. Write the output of python scripts directly to files.
    - `sqlite3`: A command-line interface for interacting with SQLite databases.

    Security Constraints:
    1.  Never access or exfiltrate data outside the /data directory.
    2.  Never delete any files or directories.
    3.  Only write to files within the /data directory.

    Input: {task_description}

    Output: JSON formatted instruction set.  Example:

    ```json
    {{
        "steps": [
            {{
                "action": "call_function",
                "name": "run_datagen",
                "parameters": {{
                    "user_email": "test@example.com"
                }}
            }},
            {{
                "action": "call_function",
                "name": "format_markdown",
                "parameters": {{
                    "file_path": "/data/format.md",
                    "prettier_version": "3.4.2"
                }}
            }}
        ]
    }}
    ```

    Make your instruction set simple and efficient as possible. Return ONLY valid JSON.  Do not add commentary or explainations.
    """

    llm_response = call_llm(prompt)

    try:
        instructions = json.loads(llm_response)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON received from LLM: {llm_response}")

    if not isinstance(instructions, dict) or "steps" not in instructions:
        raise ValueError("Invalid instruction format from LLM.  Must be a dict with a 'steps' key.")

    for step in instructions["steps"]:
        await execute_step(step)  # Await execution of each step

async def execute_step(step: dict):
    """Executes a single step from the instruction set."""
    action = step.get("action")

    if action == "run_shell_command":
        command = step.get("command")
        if not command:
            raise ValueError("Missing 'command' in run_shell_command step.")
        await run_shell_command(command)

    elif action == "call_python_script":
        script = step.get("script")
        if not script:
            raise ValueError("Missing 'script' in call_python_script step.")
        await call_python_script(script)

    elif action == "install_package":
        package = step.get("package")
        await install_package(package)

    elif action == "call_function":
        function_name = step.get("name")
        parameters = step.get("parameters", {})  # Get parameters, default to empty dict
        await call_task_function(function_name, parameters)

    else:
        raise ValueError(f"Unknown action: {action}")

async def call_task_function(function_name: str, parameters: dict):
    """Calls the task function based on the function name."""
    if function_name == "run_datagen":
        user_email = parameters.get("user_email")
        if not user_email:
            raise ValueError("Missing 'user_email' in parameters for run_datagen.")
        run_datagen(user_email)

    elif function_name == "format_markdown":
        file_path = parameters.get("file_path")
        prettier_version = parameters.get("prettier_version", "3.4.2")  # Default version
        if not file_path:
            raise ValueError("Missing 'file_path' in parameters for format_markdown.")
        format_markdown(file_path, prettier_version)

    elif function_name == "count_wednesdays":
        file_path = parameters.get("file_path")
        if not file_path:
             raise ValueError("Missing 'file_path' in parameters for count_wednesdays")
        count_wednesdays(file_path)

    elif function_name == "sort_contacts":
        file_path = parameters.get("file_path")
        if not file_path:
            raise ValueError("Missing 'file_path' in parameters for sort_contacts")
        sort_contacts(file_path)

    elif function_name == "write_recent_logs":
        log_dir = parameters.get("log_dir")
        if not log_dir:
            raise ValueError("Missing 'log_dir' in parameters for write_recent_logs")
        write_recent_logs(log_dir)

    elif function_name == "create_markdown_index":
        docs_dir = parameters.get("docs_dir")
        if not docs_dir:
            raise ValueError("Missing 'docs_dir' in parameters for create_markdown_index")
        create_markdown_index(docs_dir)

    elif function_name == "extract_email_from_llm":
        email_file = parameters.get("email_file")
        if not email_file:
            raise ValueError("Missing 'email_file' in parameters for extract_email_from_llm")
        extract_email_from_llm(email_file)

    elif function_name == "extract_credit_card_from_llm":
        image_file = parameters.get("image_file")
        if not image_file:
            raise ValueError("Missing 'image_file' in parameters for extract_credit_card_from_llm")
        extract_credit_card_from_llm(image_file)

    elif function_name == "find_similar_comments":
        comments_file = parameters.get("comments_file")
        if not comments_file:
            raise ValueError("Missing 'comments_file' in parameters for find_similar_comments")
        find_similar_comments(comments_file)

    elif function_name == "calculate_gold_ticket_sales":
        db_file = parameters.get("db_file")
        if not db_file:
            raise ValueError("Missing 'db_file' in parameters for calculate_gold_ticket_sales")
        calculate_gold_ticket_sales(db_file)

    # Phase B Tasks (Placeholders)
    elif function_name == "fetch_data_from_api":
        api_url = parameters.get("api_url")
        output_file = parameters.get("output_file")
        if not api_url or not output_file:
            raise ValueError("Missing 'api_url' or 'output_file' in parameters for fetch_data_from_api")
        fetch_data_from_api(api_url, output_file)

    elif function_name == "clone_git_repo":
        repo_url = parameters.get("repo_url")
        destination_dir = parameters.get("destination_dir")
        if not repo_url or not destination_dir:
            raise ValueError("Missing 'repo_url' or 'destination_dir' in parameters for clone_git_repo")
        clone_git_repo(repo_url, destination_dir)

    elif function_name == "run_sql_query":
        db_file = parameters.get("db_file")
        query = parameters.get("query")
        output_file = parameters.get("output_file")
        if not db_file or not query or not output_file:
            raise ValueError("Missing 'db_file' or 'query' or 'output_file' in parameters for run_sql_query")
        run_sql_query(db_file, query, output_file)

    elif function_name == "scrape_website":
        url = parameters.get("url")
        output_file = parameters.get("output_file")
        if not url or not output_file:
            raise ValueError("Missing 'url' or 'output_file' in parameters for scrape_website")
        scrape_website(url, output_file)

    elif function_name == "compress_resize_image":
        image_file = parameters.get("image_file")
        output_file = parameters.get("output_file")
        if not image_file or not output_file:
            raise ValueError("Missing 'image_file' or 'output_file' in parameters for compress_resize_image")
        compress_resize_image(image_file, output_file)

    elif function_name == "transcribe_audio":
        audio_file = parameters.get("audio_file")
        output_file = parameters.get("output_file")
        if not audio_file or not output_file:
            raise ValueError("Missing 'audio_file' or 'output_file' in parameters for transcribe_audio")
        transcribe_audio(audio_file, output_file)

    elif function_name == "convert_markdown_to_html":
        markdown_file = parameters.get("markdown_file")
        output_file = parameters.get("output_file")
        if not markdown_file or not output_file:
            raise ValueError("Missing 'markdown_file' or 'output_file' in parameters for convert_markdown_to_html")
        convert_markdown_to_html(markdown_file, output_file)

    elif function_name == "create_api_endpoint":
        csv_file = parameters.get("csv_file")
        output_file = parameters.get("output_file")
        if not csv_file or not output_file:
            raise ValueError("Missing 'csv_file' or 'output_file' in parameters for create_api_endpoint")
        create_api_endpoint(csv_file, output_file)

    else:
        raise ValueError(f"Unknown function name: {function_name}")

async def run_shell_command(command: str):
    """
    Executes a shell command.  Applies security constraints.
    """

    # Security checks before execution.
    if "rm " in command or "mv " in command:
        raise ValueError("Deletion or movement of files is not allowed.")

    # More advanced check to prevent writing outside /data, needs improvement.
    if ">" in command and not DATA_DIR in command:
        raise ValueError("Output redirection must be within the /data directory.")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, cwd=DATA_DIR)
        print(f"Command output: {result.stdout}")  # Log the output for debugging
    except subprocess.CalledProcessError as e:
        raise Exception(f"Command failed: {e.stderr}")

async def call_python_script(script: str):
    """
    Executes a python script.
    """
    try:
        result = subprocess.run(["python", "-c", script], capture_output=True, text=True, check=True, cwd=DATA_DIR)
        print(f"Script output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Python script failed: {e.stderr}")