import json
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.enums import FieldType
from app.models.questionnaire_category import QuestionnaireCategory
from app.models.questionnaire_field import QuestionnaireField
from app.models.questionnaire_subcategory import QuestionnaireSubCategory


class FieldIn(BaseModel):
    name: str
    label: str
    description: str
    order_position: int
    field_type: FieldType
    field_unit: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool
    allow_custom: bool = False
    children: list["FieldIn"] = []


class SubCategoryIn(BaseModel):
    name: str
    label: str
    description: str = ""
    order_position: int
    fields: list[FieldIn] = []


class CategoryIn(BaseModel):
    name: str
    label: str
    description: str = ""
    image_url: Optional[str] = None
    order_position: int
    sub_categories: list[SubCategoryIn] = []


if __name__ == "__main__":
    file_path: str = "resources/form_fields.json"
    all_cats = json.load(open(file_path))

    try:
        sess = SessionLocal()
        # Delete all previous rows
        print("🗑️  Cleaning existing Questionnaire data...")
        sess.execute(delete(QuestionnaireField))
        sess.execute(delete(QuestionnaireSubCategory))
        sess.execute(delete(QuestionnaireCategory))
        sess.commit()

        print("📝 Processing categories and fields...")

        for cat_data in all_cats:
            print("-" * 60)
            print(f"📋 Processing category: {cat_data['label']}")
            cat_in = CategoryIn.model_validate(cat_data)
            cat = QuestionnaireCategory(**cat_in.model_dump(exclude=["sub_categories"]))

            for sub_cat_in in cat_in.sub_categories:
                sub_cat = QuestionnaireSubCategory(
                    **sub_cat_in.model_dump(exclude=["fields"]),
                )
                cat.sub_categories.append(sub_cat)

                for parent_field_in in sub_cat_in.fields:
                    parent_field = QuestionnaireField(
                        **parent_field_in.model_dump(exclude=["children"]),
                    )
                    sub_cat.fields.append(parent_field)

                    # we just need to go 1 level deeper (no need for recursivity)
                    for child_field_in in parent_field_in.children:
                        child_field = QuestionnaireField(
                            **child_field_in.model_dump(exclude=["children"]),
                        )
                        parent_field.children.append(child_field)

            sess.add(cat)

        sess.commit()
        print("\n🎉 Successfully seeded questionnaire categories and fields!")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        if hasattr(e, "args"):
            print(f"Error details: {e.args}")
        sess.rollback()
    finally:
        sess.close()
