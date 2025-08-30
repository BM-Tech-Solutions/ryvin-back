from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.questionnaire_category import QuestionnaireCategory
from app.models.questionnaire_field import QuestionnaireField

if __name__ == "__main__":
    try:
        sess = SessionLocal()
        # Delete all previous rows
        print("🗑️  Cleaning existing questionnaire data...")
        sess.execute(delete(QuestionnaireField))
        sess.execute(delete(QuestionnaireCategory))
        sess.commit()
        print("Done")

    except Exception as e:
        print(f"\n❌ Error during cleaning: {e}")
        if hasattr(e, "args"):
            print(f"Error details: {e.args}")
        sess.rollback()
    finally:
        sess.close()
