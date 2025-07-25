import json
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.enums import FieldType
from app.models.questionnaire_category import QuestionnaireCategory
from app.models.questionnaire_field import QuestionnaireField


class CategorySchema(BaseModel):
    name: str
    label: str
    description: str = ""
    order_position: int
    step: int
    fields: list = []


class FieldSchema(BaseModel):
    name: str
    label: str
    description: str
    order_position: int
    field_type: FieldType
    parent_field: Optional[str] = None
    field_unit: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool
    allow_custom: bool = False
    child_fields: list = []


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
            cat_in = CategorySchema.model_validate(cat_in)
            new_cat = QuestionnaireCategory(**cat_in.model_dump(exclude=["fields"]))
            for field_in in cat_in.fields:
                field_in = FieldSchema.model_validate(field_in)
                new_cat.fields.append(
                    QuestionnaireField(
                        **field_in.model_dump(exclude=["child_fields"]),
                        category_id=new_cat.id,
                    )
                )
                for field_in in field_in.child_fields:
                    field_in = FieldSchema.model_validate(field_in)
                    new_cat.fields.append(
                        QuestionnaireField(
                            **field_in.model_dump(exclude=["child_fields"]),
                            category_id=new_cat.id,
                        )
                    )

            sess.add(new_cat)

        sess.commit()
    except Exception as e:
        print(e)
        print(e.args)
    finally:
        sess.close()
