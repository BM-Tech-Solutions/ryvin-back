# Ryvin Backend

Backend for Ryvin, a serious dating application with a structured journey approach to foster authentic and lasting relationships.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **Migrations**: Alembic
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT + OAuth2
- **Validation**: Pydantic V2
- **Documentation**: OpenAPI/Swagger automatic

## Project Structure

```
backend/
├── app/
│   ├── core/           # Configuration, security, middleware
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── api/            # API endpoints
│   ├── services/       # Business logic
│   ├── utils/          # Utilities
│   └── alembic/        # Migrations
├── tests/
└── requirements.txt
```

## Getting Started

### Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables (copy `.env.example` to `.env` and adjust as needed)
6. Run migrations: `alembic upgrade head`
7. Start the server: `uvicorn app.main:app --reload`

### Using Docker

1. Clone the repository
2. Make sure Docker and Docker Compose are installed
3. Build and start the containers:
   ```
   docker-compose up -d --build
   ```
4. The API will be available at `http://localhost:8000`
5. To run migrations manually:
   ```
   docker-compose run --rm migrations
   ```
6. To create a new migration after model changes:
   ```
   docker-compose run --rm web alembic revision --autogenerate -m "Description of changes"
   ```
7. To stop the containers:
   ```
   docker-compose down
   ```

## API Documentation

Once the server is running, access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Features

- User authentication with JWT
- User profile management
- Compatibility questionnaire
- Matching algorithm
- Structured journey process
- Messaging system
- Meeting requests and feedback
