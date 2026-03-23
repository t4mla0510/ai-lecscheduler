# LecScheduler - University Scheduling System

LecScheduler is an automated university lecture scheduling system powered by a Genetic Algorithm. It aims to generate optimal schedules by considering various constraints like lecturer availability, room capacity, and course requirements.

## Features
- GA-based Scheduling Engine: Efficiently solves complex scheduling problems.
- Modern Web Interface: Built with React and TypeScript for a smooth user experience.
- FastAPI Backend: High-performance API layer handling scheduling logic.
- Docker Support: Easy deployment and development environment setup.

## Prerequisites
Before you begin, ensure you have the following installed:
- Node.js: Version 18.0.0 or higher.
- Python: Version 3.11 or higher.
- uv: The "extremely fast Python package installer and resolver".
  - Install via PowerShell (Windows):
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

## Local Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai_project
   ```

2. Environment Configuration:
   The frontend requires an environment file to communicate with the backend API.
   - Copy the example environment file:
     ```bash
     cp frontend/.env.example frontend/.env
     ```
   - By default, `VITE_API_URL` is set to `http://localhost:5001/api`.

3. Run the all-in-one setup:
   This command installs Node.js dependencies for the root and frontend, and sets up the Python virtual environment for the backend.
   ```bash
   npm run setup:all
   ```

## Running the Application

To start both the backend and frontend in development mode with hot-reloading:
```bash
npm run dev
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:5001](http://localhost:5001)
- API Documentation: [http://localhost:5001/docs](http://localhost:5001/docs)

## Docker Setup

To run the entire stack using Docker:
```bash
docker-compose up --build -d
```
This will containerize the application and expose:
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:5001](http://localhost:5001)

---
*Developed for Fundamentals of Artificial Intelligence.*