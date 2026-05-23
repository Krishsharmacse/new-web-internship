# Closira Backend Prototype

This is a lightweight backend service simulating Closira's core customer enquiry-handling workflow.

## Tech Stack
- Python 3.10+
- FastAPI
- SQLAlchemy
- Pydantic
- python-json-logger

## Setup and Run Instructions

1. Ensure you have MongoDB running locally on `localhost:27017` (or change the connection string in `.env` / `app/config.py`).
   - If using docker: `docker run -d -p 27017:27017 --name mongo mongo`
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the API server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. View API docs at: `http://localhost:8000/docs`

## Data Structure & DSA Optimization
- **Database Choice (MongoDB):** Selected MongoDB because document databases align well with the unstructured and dynamic nature of communication logs and event history. It allows seamless storing of polymorphic events in the `history` collection without strict schema migrations.
- **SOP Matching (Trie Data Structure):** Used a Trie (Prefix Tree) in `app/services/sop_matcher.py`. Instead of iterating through all keywords for each SOP sequentially using `.find()` or Regex (which is O(N*M)), the Trie optimizes keyword matching to O(K) where K is the text length, making the substring search much more efficient as the number of SOP keywords grows.

## Background Processing Choice
- **FastAPI BackgroundTasks vs Celery:** 
  For this prototype, **FastAPI BackgroundTasks** was chosen.
  **Reasoning:** Celery requires additional infrastructure (Redis/RabbitMQ as a broker and Celery worker processes). FastAPI's built-in BackgroundTasks runs in the same event loop, making it significantly more lightweight and perfect for a simple simulation, avoiding the overhead of external dependencies while still achieving non-blocking asynchronous processing for the client.

## Endpoints

Test the API via Postman, `/docs`, or use the provided `test_api.http` file.

- `GET /health`
- `POST /enquiry`
- `POST /enquiry/{id}/followup`
- `POST /enquiry/{id}/escalate`
- `GET /enquiry/{id}/history`

## Trade-offs & Limitations
- **Background Tasks Resilience:** FastAPI background tasks are lost if the server restarts before they execute. In a production environment with long-running tasks or guaranteed execution requirements, a robust task queue like Celery or Temporal is necessary.
- **Auth:** No authentication is implemented.
- **Pagination:** History endpoint returns a hard limit of 100 entries. True production APIs would require cursor-based pagination.
