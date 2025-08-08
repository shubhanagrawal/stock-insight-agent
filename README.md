# AI Stock Insight Agent for the Indian Market 🇮🇳

**An autonomous agent that analyzes real-time financial news from the Indian market and converts it into actionable investment insights.**

---

**[➡️ View the Live Demo Here]** `(Link to your deployed Streamlit app)`

![GIF of the app in action] `(HIGHLY RECOMMENDED: Record a short GIF of your app and add it here)`

---

## 🎯 The Problem

The financial news cycle is a firehose of information. For any investor, the challenge isn't finding news; it's finding the **signal within the noise**. A single headline about a company's earnings, a promoter's stake sale, or a new contract can have a significant market impact, but it's buried among dozens of other, less important articles.

This project builds an AI agent to solve this problem. It autonomously monitors the news, identifies the key players, understands the sentiment, and generates a concise, analytical insight, mimicking the workflow of a junior financial analyst.

## ✨ Features

* **Automated News Scraping:** The agent monitors the Economic Times RSS feed for the latest market news.
* **Hybrid Ticker Extraction:** It uses a robust, two-step process to identify companies:
    1.  **Local Knowledge Base:** A high-speed check against a manually curated list of prominent Indian companies for maximum accuracy.
    2.  **LLM Fallback:** If a company isn't in the local list, it uses the Groq API (running Llama 3) to perform advanced entity recognition, allowing it to identify new or less common companies.
* **Sentiment Analysis:** It leverages a `FinBERT` model, specifically fine-tuned for financial text, to accurately classify news headlines as `Positive`, `Negative`, or `Neutral`.
* **Insight Generation:** It synthesizes all the gathered information into a clean, human-readable "Insight Card" that summarizes the potential impact on the identified company.

## ⚙️ System Architecture

The agent operates on a simple, 4-stage pipeline:

`Scrape News -> Extract Tickers -> Analyze Sentiment -> Generate Insight`

![A simple flowchart showing the 4 stages of the pipeline] `(Create a simple diagram and add it here)`

### **Tech Stack**

* **Data Acquisition:** `requests`, `feedparser`, `beautifulsoup4`
* **Core NLP & Inference:**
    * **Entity Extraction:** Groq API (Llama 3 8B)
    * **Sentiment Analysis:** Hugging Face Inference API (ProsusAI/finbert)
* **Orchestration & UI:** Python, Streamlit
* **Environment:** `python-dotenv` for managing API keys

## 🚀 How to Run It Locally

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/shubhanagrawal/stock-insight-agent.git](https://github.com/shubhanagrawal/stock-insight-agent.git)
    cd stock-insight-agent
    ```

2.  **Set up a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create your `.env` file:**
    * Create a file named `.env` in the root of the project.
    * Add your API keys to this file:
        ```
        GROQ_API_KEY="YOUR_GROQ_KEY_HERE"
        HUGGINGFACE_API_TOKEN="YOUR_HUGGINGFACE_TOKEN_HERE"
        ```

5.  **Run the command-line version:**
    ```bash
    python app.py
    ```

6.  **Launch the Web Dashboard:**
    ```bash
    streamlit run dashboard.py
    ```

## 🔮 Future Improvements

* **Sophisticated Rationale:** Upgrade the inference engine to generate a more detailed rationale for its insights instead of a static sentence.
* **Vector Database for Similarity:** Store article embeddings in a vector DB to find related news or detect recurring themes over time.
* **Portfolio Simulation:** Allow users to input a hypothetical portfolio and see which of their stocks were mentioned in the latest news cycle.
