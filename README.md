# Fake News Validator

This application validates news headlines using the Llama-4 model from Groq, Brave Search API, and Selenium web scraping. It uses function calling to search for relevant news sources and analyze their content to determine the veracity of a given headline.

## Features

-   News headline validation.
-   Integration with Groq's Llama-4 for analysis.
-   Brave Search API for finding relevant news articles.
-   Selenium for web scraping article content.
-   Streamlit interface for user interaction.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:** (Optional but recommended)
    ```bash
    python -m venv my_env
    # On Windows
    .\my_env\Scripts\activate
    # On macOS/Linux
    source my_env/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    Create a `.env` file in the root directory and add your API keys:
    ```env
    GROQ_API_KEY="YOUR_GROQ_API_KEY"
    BRAVE_API_KEY="YOUR_BRAVE_API_KEY"
    ```
    You will also need to ensure you have a compatible WebDriver (like ChromeDriver) installed and its path accessible or configured if needed by Selenium.

## Usage

Run the Streamlit application:

```bash
streamlit run app.py
```

Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`). Enter a news headline in the input field and click "Validate" to start the analysis.
