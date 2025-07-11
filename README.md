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
1. make sure "uv" is installed: `pip install uv`
1. Create a virtual environment & Install dependencies: `uv sync`
1. make sure "pre-commit" hooks are installed: `uv run pre-commit install`
1. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
1. Set up environment variables (copy `.env.example` to `.env` and adjust as needed)
1. Run migrations: `alembic upgrade head`
1. Start the server: `uvicorn app.main:app --reload`

#### about **uv**:
* built with rust, that means it's fast
* to install/uninstall a new dependency: `uv add new-dependecy` or `uv remove new-dependecy`
* you can use `uv pip install` but `uv add` is better
* uses "pyproject.toml" + "uv.lock" instead of "requirements.txt"
* to create "requirements.txt" from pyproject.toml: `uv pip compile pyproject.toml -o requirements.txt`
* `uv run main.py` does 3 things:
   1. activates venv
   1. runs main.py
   1. deactivates venv

#### about **ruff**:
* built with rust, that means it's fast
* replaces: flake8, black, isort
* config file: "ruff.toml"

#### about **pre-commit**:
* install the hooks using: `uv run pre-commit install`
* standard way to enforce checks (like linting, formatting, etc.) before each Git commit.
* config file: ".pre-commit-config.yaml"

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
