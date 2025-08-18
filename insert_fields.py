import json
import os
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.enums import FieldType
from app.models.questionnaire_category import QuestionnaireCategory
from app.models.questionnaire_field import QuestionnaireField


class SubcategorySchema(BaseModel):
    name: str
    label: str
    description: str = ""
    order_position: int
    fields: list = []


class CategorySchema(BaseModel):
    name: str
    label: str
    description: str = ""
    order_position: int
    step: int
    fields: list = []  # For backward compatibility
    subcategories: Optional[list] = None  # For new structure


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


def load_form_fields():
    """Load form fields from updated file first, then fallback to original"""
    # Try updated file first
    if os.path.exists("resources/form_fields_updated.json"):
        print("📋 Loading from form_fields_updated.json (with subcategories)")
        return json.load(open("resources/form_fields_updated.json"))
    
    # Fallback to original file
    print("📋 Loading from form_fields.json (legacy format)")
    return json.load(open("resources/form_fields.json"))


def process_fields_from_subcategories(category_data, new_cat, sess):
    """Process fields from subcategories structure"""
    for subcategory_data in category_data.get("subcategories", []):
        print(f"  📂 Processing subcategory: {subcategory_data['label']}")
        
        for field_data in subcategory_data.get("fields", []):
            field_schema = FieldSchema.model_validate(field_data)
            new_field = QuestionnaireField(
                **field_schema.model_dump(exclude=["child_fields"]),
                category_id=new_cat.id,
            )
            new_cat.fields.append(new_field)
            print(f"    ✅ Field '{field_data['name']}' - ID: {new_field.id}")
            
            # Handle child fields
            for child_field_data in field_schema.child_fields:
                child_field_schema = FieldSchema.model_validate(child_field_data)
                child_field = QuestionnaireField(
                    **child_field_schema.model_dump(exclude=["child_fields"]),
                    category_id=new_cat.id,
                )
                new_cat.fields.append(child_field)
                print(f"    ✅ Child field '{child_field_data['name']}' - ID: {child_field.id}")


def process_fields_legacy(category_data, new_cat, sess):
    """Process fields from legacy structure (fields directly in category)"""
    for field_data in category_data.get("fields", []):
        field_schema = FieldSchema.model_validate(field_data)
        new_field = QuestionnaireField(
            **field_schema.model_dump(exclude=["child_fields"]),
            category_id=new_cat.id,
        )
        new_cat.fields.append(new_field)
        print(f"    ✅ Field '{field_data['name']}' - ID: {new_field.id}")
        
        # Handle child fields
        for child_field_data in field_schema.child_fields:
            child_field_schema = FieldSchema.model_validate(child_field_data)
            child_field = QuestionnaireField(
                **child_field_schema.model_dump(exclude=["child_fields"]),
                category_id=new_cat.id,
            )
            new_cat.fields.append(child_field)
            print(f"    ✅ Child field '{child_field_data['name']}' - ID: {child_field.id}")


if __name__ == "__main__":
    cats = load_form_fields()
    
    try:
        sess = SessionLocal()
        # Delete all previous rows
        print("🗑️  Cleaning existing questionnaire data...")
        sess.execute(delete(QuestionnaireField))
        sess.execute(delete(QuestionnaireCategory))
        sess.commit()

        print("📝 Processing categories and fields...")
        
        for cat_data in cats:
            print("-" * 60)
            print(f"📋 Processing category: {cat_data['label']}")
            
            # Create category (excluding fields and subcategories from direct mapping)
            cat_schema = CategorySchema.model_validate(cat_data)
            new_cat = QuestionnaireCategory(
                **cat_schema.model_dump(exclude=["fields", "subcategories"])
            )
            
            # Process fields based on structure
            if cat_data.get("subcategories"):
                # New structure with subcategories
                process_fields_from_subcategories(cat_data, new_cat, sess)
            else:
                # Legacy structure with direct fields
                process_fields_legacy(cat_data, new_cat, sess)
            
            sess.add(new_cat)
            print(f"  ✅ Added {len(new_cat.fields)} fields to category '{cat_data['name']}'")

        sess.commit()
        print("\n🎉 Successfully seeded questionnaire categories and fields!")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        if hasattr(e, 'args'):
            print(f"Error details: {e.args}")
        sess.rollback()
    finally:
        sess.close()
