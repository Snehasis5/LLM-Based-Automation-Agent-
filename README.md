## Overview

Operation teams often process large volumes of log files, reports, and code artifacts to generate actionable insights for internal stakeholders. Due to the unpredictable nature of incoming data (from logs, ticket systems, source code, surveys, etc.) I have used a Large Language Model (LLM) as an intermediate transformer. In this role, the LLM will perform reasonably deterministic tasks. This LLM based automation agent will automate some of the routine tasks:

## Features  
- Accepts plain-English tasks via API.  
- Executes tasks using internal logic and LLM assistance.  
- Verifies output against pre-computed results.  
- Handles operational tasks like data formatting, sorting, extraction, and processing.  
- Ensures data security by restricting access outside `/data` and preventing deletion.  
- Capable of handling business tasks such as API fetching, git operations, SQL queries, web scraping, image processing, and more.  

---

## Endpoints  
### 1. POST /run?task=<task description>  
- Executes the specified task.  
- **Responses:**  
  - `200 OK` - Success  
  - `400 Bad Request` - Task error  
  - `500 Internal Server Error` - Agent error  

### 2. GET /read?path=<file path>  
- Returns the content of the specified file for verification.  
- **Responses:**  
  - `200 OK` - Success  
  - `404 Not Found` - File not found  

---

## Getting Started  
### Prerequisites  
- Python 3.8+  
- Docker (optional, for containerized deployment)  
- An OpenAI API key (if using LLM)  

---

### Installation  
1. **Clone the Repository:**  
    ```bash
    git clone <repository-url>
    cd project-repo
    ```

2. **Create a Virtual Environment:**  
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate
    ```

3. **Install Dependencies:**  
    ```bash
    pip install -r requirements.txt
    ```

4. **Environment Variables:**  
    Create a `.env` file with the following:  
    ```env
    OPENAI_API_KEY=your_openai_api_key
    ```

---

### Running the Application  
**Locally:**  
```bash
uvicorn api:app --reload