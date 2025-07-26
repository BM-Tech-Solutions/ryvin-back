1) stop the old compose stack
2) switch to & pull the new branch "dev-migrate-sqlalchemy"
3) update ".env" from ".env.example" (copy/paste & adjust)
4) launch the posgresql container (no "migrations" or "web" just yet)
5) run these commands:
    1) if you're applying these commands from outside docker:
        1) activate the venv: `source .venv/bin/activate`
        2) install new dependencies: `pip install -r requirements.txt`
        3) set these env vars:
        `export POSTGRES_SERVER=localhost`
        `export POSTGRES_PORT=5433`

    2) drop all tables: `python drop_db.py`

    3) run new migrations to recreate new tables: `python alembic upgrade head`

    4) insert Questionnaire fields and their metadata: `python insert_fields.py`

6) now launch the "web" service
