
# 💹 AI Stock Insight Agent – Real-time NLP-powered Market Sentiment Analyzer for Indian Stocks 🇮🇳

**An autonomous AI system that ingests, analyzes, and quantifies real-time Indian financial news — transforming unstructured market data into validated, data-driven investment insights.**

---

## 🌐 [🎥 Live Demo (Streamlit App)](https://your-demo-link-here.com)

*(💡 Tip: Upload a short demo GIF in `/assets/demo.gif` and embed it below for maximum visual impact)*

```markdown
![AI Stock Insight Demo](assets/demo.gif)
```

---

## 🎯 Problem Statement

Financial news is abundant — but actionable insights are buried in noise.
This project solves that by building an **AI agent** that behaves like a **junior financial analyst**:
it reads, comprehends, analyzes, and reports **market-moving** information — autonomously.

---

## ⚙️ System Overview

The system continuously performs this loop:
**Ingest → Process (NLP) → Store → Backtest → Visualize**

✅ Fetches and cleans real-time financial news (NSE/BSE, MoneyControl, ET, Mint)
✅ Extracts company tickers with high accuracy (NER + NSE validation)
✅ Evaluates sentiment using `FinBERT` (financially tuned BERT model)
✅ Persists all results to SQLite for historical tracking
✅ Backtests prediction validity against stock price data (`yfinance`)
✅ Displays real-time and historical insights on an interactive Streamlit dashboard

---

## ✨ Key Features

| Feature                                      | Description                                                        |
| -------------------------------------------- | ------------------------------------------------------------------ |
| 📰 **Multi-source News Ingestion**           | Curated RSS and web feeds from top Indian financial sources        |
| 🏷️ **Ticker Extraction (NER + Validation)** | spaCy NER + cross-check with official NSE stock list               |
| 🤖 **Financial Sentiment Analysis**          | FinBERT model (Hugging Face) for context-aware financial sentiment |
| 💾 **Persistent Data Storage**               | SQLite-based local database for all insights                       |
| 📊 **Quantitative Backtesting Engine**       | Validates model predictions vs. real stock performance             |
| 🧠 **Streamlit Dashboard**                   | Interactive real-time visualization of sentiment trends            |

---

## 📈 Example Quantitative Results

| Ticker     | Date       | Predicted Sentiment | Next Day Return | Correct? |
| ---------- | ---------- | ------------------- | --------------- | -------- |
| BAJFINANCE | 2025-10-06 | Positive            | +0.76%          | ✅        |
| RELIANCE   | 2025-10-07 | Positive            | -0.21%          | ❌        |
| INFY       | 2025-10-08 | Negative            | -1.15%          | ✅        |

> An **accuracy >50%** over a large sample indicates a **statistically meaningful predictive edge**.

---

## 🧩 Tech Stack

| Layer             | Technologies                                     |
| ----------------- | ------------------------------------------------ |
| **Frontend**      | Streamlit                                        |
| **Backend**       | Python                                           |
| **NLP & AI**      | spaCy (`en_core_web_lg`), FinBERT (Hugging Face) |
| **Data Handling** | Pandas, BeautifulSoup, Feedparser                |
| **Finance APIs**  | yFinance                                         |
| **Database**      | SQLite                                           |
| **Orchestration** | dotenv, requests                                 |
| **Backtesting**   | pandas-ta / custom comparison scripts            |

---

## 🧰 Installation Guide

1️⃣ **Clone the repository**

```bash
git clone https://github.com/shubhanagrawal/stock-insight-agent.git
cd stock-insight-agent
```

2️⃣ **Set up virtual environment**

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3️⃣ **Download the NLP model**

```bash
python -m spacy download en_core_web_lg
```

4️⃣ **Prepare environment**
Create a `.env` file in the root folder:

```
HUGGINGFACE_API_TOKEN=your_huggingface_token
```

5️⃣ **Run the Streamlit dashboard**

```bash
streamlit run dashboard.py
```

6️⃣ **(Optional) Run the backtester**

```bash
python backtester.py
```

---

## 🚀 Future Enhancements

* [ ] **Celery + Redis Integration:** Move analysis to async background tasks
* [ ] **Dockerization:** Deploy in a portable, production-ready container
* [ ] **PostgreSQL Migration:** Scale data storage beyond SQLite
* [ ] **Auto Stock Watchlist Generator:** Dynamically track trending tickers
* [ ] **LLM Integration:** Summarize market news in human-readable insights

---

## 🧠 Why This Project Stands Out

This project demonstrates:

* **AI + Finance understanding** — bridging NLP with quantitative validation
* **End-to-End Product Design** — from ingestion to visualization
* **Quantitative rigor** — validated model accuracy, not just text processing
* **Professional-grade modular code** — maintainable, extensible, and reproducible

---

## 👤 Author

**Shubhan Agrawal**
🎓 B.Tech CSE, MIT World Peace University, Pune
💼 Data Science | NLP | Quantitative Finance | AI Systems
🔗 [GitHub](https://github.com/shubhanagrawal) • [LinkedIn](https://linkedin.com/in/shubhanagrawal)



## ⭐ Star This Repo

If this project inspired you or showcased useful ideas — please consider giving it a ⭐!

<p align="center">
  <img src="https://img.shields.io/github/stars/shubhanagrawal/stock-insight-agent?style=social" />
</p>



Where AI meets Market Intelligence — turning news into numbers.


