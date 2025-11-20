#!/bin/sh
set -e

# Get the first argument which should be the service name
SERVICE_TYPE=$1

# Run migrations only if this is the migrations service
if [ "$SERVICE_TYPE" = "migrations" ]; then
  echo "Running database migrations..."
  alembic upgrade head
  echo "Migrations completed successfully!"
  echo "Checking if questionnaire metadata needs seeding..."
  python - << 'PY'
import os
from app.core.database import SessionLocal
from app.models.questionnaire_category import QuestionnaireCategory

sess = SessionLocal()
try:
    count = sess.query(QuestionnaireCategory).count()
    if count == 0:
        print("Seeding questionnaire categories and fields from resources/form_fields_updated.json ...")
        import importlib.util, sys
        script_path = os.path.join(os.getcwd(), "insert_fields.py")
        if not os.path.exists(script_path):
            print("insert_fields.py not found; skipping seeding.")
        else:
            spec = importlib.util.spec_from_file_location("insert_fields", script_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            print("Seeding finished.")
    else:
        print(f"Questionnaire metadata already present (categories: {count}). Skipping seeding.")
finally:
    sess.close()
PY
  exit 0
fi

# For the web service, just start the application
echo "Starting application..."
exec "$@"
