import json

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.questionnaire_category import QuestionnaireCategory
from app.models.questionnaire_field import QuestionnaireField

if __name__ == "__main__":
    cats = json.load(open("resources/form_fields.json"))
    try:
        sess = SessionLocal()
        # delete all previous rows
        sess.execute(delete(QuestionnaireField))
        sess.execute(delete(QuestionnaireCategory))

        for cat_in in cats:
            print("-" * 50)
            print(cat_in["name"])
            fields = cat_in.pop("fields", [])
            new_cat = QuestionnaireCategory(**cat_in)
            for field_in in fields:
                new_cat.fields.append(QuestionnaireField(**field_in))

            sess.add(new_cat)

        sess.commit()
    except Exception as e:
        print(e)
        print(e.args)
    finally:
        sess.close()
