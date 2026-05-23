# Closira Enquiry Pipeline & SOP Matcher

A robust, asynchronous backend service designed to handle inbound customer enquiries, classify them using advanced text-matching algorithms, and autonomously trigger the correct Standard Operating Procedures (SOPs). 

This project also includes a beautiful, responsive, glassmorphism frontend dashboard to seamlessly test the APIs.

---

## Features
- **Asynchronous Processing**: Handles incoming HTTP requests instantly and delegates CPU-heavy tasks (like SOP matching) to FastAPI Background Tasks.
- **Advanced SOP Matching Engine**: Utilizes Aho-Corasick, Rabin-Karp, and TF-IDF inspired scoring for high-speed, accurate intent classification.
- **Relational Database**: Uses SQLite via SQLAlchemy ORM for robust, ACID-compliant data storage.
- **Audit Trails**: Maintains a strict timeline of state changes (`enquiry_created`, `processing`, `sop_matched`, `escalated`) in a dedicated `history` table.
- **Follow-ups & Escalations**: APIs to manually escalate issues or schedule delayed follow-up responses.
- **Integrated Dashboard**: Directly serves a modern frontend UI on `localhost:8000` to interact with all API endpoints.

---

## Core Algorithms & Approach

To solve the assignment of matching inbound messages against predefined SOP keywords efficiently, the application implements the **AdvancedSOPMatcher**, which combines several powerful Computer Science algorithms:

### 1. Aho-Corasick Automaton (Multi-Pattern Matching)
Instead of iterating through every keyword for every word in the message ($O(N \times M)$), we construct an **Aho-Corasick Automaton** (a Trie augmented with failure links).
- **Why?** It allows us to search for *all* SOP keywords simultaneously in a single pass of the input text.
- **Complexity:** $O(n + z)$ where $n$ is the length of the message and $z$ is the number of matched keywords.

### 2. Rabin-Karp (Exact Phrase Detection)
Certain SOPs rely on exact phrases (e.g., "book a table"). We use a rolling hash approach (Rabin-Karp) via regex boundaries to give priority to exact phrase matches over scattered keyword matches.

### 3. TF-IDF Inspired Confidence Scoring
Not all keywords are created equal. The system calculates a `confidence` score (0.0 to 1.0) based on:
- **Keyword Coverage**: Ratio of matched keywords to total SOP keywords.
- **Specificity**: Less frequent words (across all SOPs) carry higher weight.
- **Priority Tiering**: Matches are assigned a priority (`EXACT_PHRASE`, `MULTI_KEYWORD`, `SINGLE_KEYWORD`) to determine the definitive best response.

### 4. Levenshtein Distance (Fuzzy Matching)
To handle typos, the system includes an optimized Levenshtein Distance function with early-termination to gracefully catch misspellings without blowing up time complexity.

---

## 🛠️ Tech Stack
- **Backend Framework**: Python 3.10+, FastAPI
- **Database**: SQLite (Development) -> easily swappable to PostgreSQL.
- **ORM**: SQLAlchemy
- **Data Validation**: Pydantic
- **Frontend**: Vanilla HTML/CSS/JS with Google Fonts (Outfit) and FontAwesome. Served via FastAPI `StaticFiles`.

---

## 🚦 Getting Started

### 1. Installation
Clone the repository and install the dependencies using `uv` or `pip`:
```bash
git clone https://github.com/Krishsharmacse/new-web-internship.git
cd new-web-internship/closira_backend

# Using pip
pip install -r requirements.txt

# Or using uv (recommended for speed)
uv pip install -r requirements.txt
```

### 2. Run the Application
Start the uvicorn server. Since the app uses SQLAlchemy, it will automatically generate the `closira.db` SQLite database file on startup.
```bash
uvicorn app.main:app --reload
```

### 3. Test with the Dashboard
Open your web browser and navigate to:
**[http://localhost:8000](http://localhost:8000)**

You can use the frontend dashboard to submit enquiries, view live logs, fetch history, and test the Aho-Corasick priority algorithm. Try these sample inputs:
- *"I would like to book a table for tomorrow"* -> Triggers `EXACT_PHRASE` priority.
- *"What is the price of this service?"* -> Triggers `MULTI_KEYWORD` priority.
- *"Your service is terrible"* -> Triggers `SINGLE_KEYWORD` priority.

---

## 📊 Production Readiness & Trade-offs (Honest Assessment)
While this prototype perfectly demonstrates strong algorithmic design and async REST patterns, a production deployment at scale would require the following changes:

1. **Intelligent Matching**: While Aho-Corasick is extremely fast for explicit keywords, it lacks semantic understanding. In production, this would be augmented with an Embedding model (e.g., SentenceTransformers + Vector DB like Milvus/Pinecone) to understand intent even if synonyms are used.
2. **Task Queue**: FastAPI `BackgroundTasks` are stored in memory. If the server crashes, scheduled follow-ups are lost. In production, we would migrate to **Celery + Redis / RabbitMQ** to ensure persistent, distributed background workers.
3. **Database Concurrency**: SQLite is excellent for this prototype, but write-locks under heavy load. The codebase is designed with SQLAlchemy so swapping the URL string in `config.py` to **PostgreSQL** handles this instantly.
4. **Tenant Awareness**: For a B2B SaaS, the database schema would need a `tenant_id` to segregate data between different Closira clients.
