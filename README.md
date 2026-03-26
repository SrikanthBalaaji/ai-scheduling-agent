# AI Scheduling Agent

AI-powered student planner with an event billboard, personal calendar, and AI-assisted scheduling.

## Tech Stack

- Backend: FastAPI
- Frontend: React (Vite)
- Database: SQLite
- Agent: LangGraph (planned)

## Project Structure

- backend/
- frontend/
- shared/

## Frontend (Vite)

### Run Frontend

```bash
npm install
npm run dev
```

### Build Frontend

```bash
npm run build
```

## Backend

### Run Backend

```bash
cd backend
uvicorn main:app --reload
```

### API Base URL

`http://localhost:8000`

## Notes

- Keep implementation minimal (hackathon scope).
- Coordinate before changing shared schemas or other modules.
