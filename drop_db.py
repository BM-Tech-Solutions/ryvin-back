from sqlalchemy import text

from app.core.database import Base, engine
from app.models import *  # noqa: F403

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)

# Ensure alembic_version table is also dropped
with engine.connect() as connection:
    try:
        connection.execute(text("DROP TABLE alembic_version;"))
        connection.commit()
    except Exception as e:
        print(f"\talembic_version table not found or could not be dropped: -{e}-")

print("All tables dropped.")
