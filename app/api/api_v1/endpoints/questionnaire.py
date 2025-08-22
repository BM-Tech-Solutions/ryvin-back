import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.models.enums import get_field_enum
from app.schemas.questionnaire import (
    QuestionnaireCreate,
    QuestionnaireInDB,
    QuestionnaireUpdate,
)
from app.services.questionnaire_service import QuestionnaireService

router = APIRouter()


@router.get(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
):
    """
    Get current user's questionnaire
    """
    quest_service = QuestionnaireService(session)
    questionnaire = quest_service.get_questionnaire(current_user.id)
    if not questionnaire:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
        )
    return QuestionnaireInDB.model_validate(questionnaire).model_dump()


@router.get(
    "/me/status",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_questionnaire_status(
    session: SessionDep,
    current_user: VerifiedUserDep,
) -> dict[str, Any]:
    """
    Get current user's questionnaire completion status.

    Returns:
        {
            "is_completed": bool,
            "missing_by_categories": [
                {
                    "id": str,  # Database UUID of the category
                    "name": str,
                    "label": str,
                    "description": str,
                    "order_position": int,
                    "step": int,
                    "picture_url": str,
                    "subcategories": [
                        {
                            "id": str,  # Composite ID: "{category_id}_{subcategory_name}"
                            "name": str,
                            "label": str,
                            "description": str,
                            "order_position": int,
                            "fields": [
                                {
                                    "id": str,  # Database UUID of the field
                                    "name": str,
                                    "label": str,
                                    "description": str,
                                    "field_type": str,
                                    "required": bool,
                                    ...
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_questionnaire(current_user.id)
    if not quest:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
        )

    # Consider any field that is None as not completed
    missing = quest_service.get_null_fields(quest)
    is_completed = len(missing) == 0

    response: dict[str, Any] = {
        "is_completed": is_completed,
        "missing_by_categories": [],
    }

    # When incomplete, also group missing fields by their categories and subcategories with full metadata
    if not is_completed:
        # Get database categories and fields for ID mapping
        db_categories = quest_service.get_questions_by_categories()
        db_field_map = {}
        db_category_map = {}

        for db_cat in db_categories:
            db_category_map[db_cat.name] = str(db_cat.id)
            for db_field in db_cat.fields:
                db_field_map[db_field.name] = str(db_field.id)

        # Try to load from updated form fields JSON with subcategories
        try:
            root = Path(__file__).resolve().parents[4]
            form_json = root / "resources" / "form_fields_updated.json"
            if form_json.exists():
                data = json.loads(form_json.read_text(encoding="utf-8"))
                missing_set = set(missing)
                categories_out: list[dict[str, Any]] = []

                # Process missing fields and organize by database categories with proper subcategory structure
                missing_set = set(missing)

                # Group missing fields by their database categories
                for category in db_categories:
                    category_missing_fields = []
                    for field in category.fields:
                        if field.name in missing_set:
                            category_missing_fields.append(field)

                    if not category_missing_fields:
                        continue

                    # Find corresponding JSON category for metadata
                    json_category = None
                    for json_cat in data:
                        if json_cat.get("name") == category.name:
                            json_category = json_cat
                            break

                    category_id = str(category.id)
                    subcategories_out = []

                    # If JSON category has subcategories, organize fields by them
                    if json_category and json_category.get("subcategories"):
                        subcategory_fields_map = {}

                        # First, map each missing field to its subcategory
                        for field in category_missing_fields:
                            found_subcategory = None
                            json_field_data = None

                            # Find which subcategory this field belongs to
                            for subcat in json_category.get("subcategories", []):
                                for json_field in subcat.get("fields", []):
                                    if json_field.get("name") == field.name:
                                        found_subcategory = subcat
                                        json_field_data = json_field
                                        break
                                if found_subcategory:
                                    break

                            # If not found in subcategories, put in general
                            if not found_subcategory:
                                found_subcategory = {
                                    "name": "general",
                                    "label": "General",
                                    "description": "",
                                    "order_position": 999,
                                }
                                json_field_data = {
                                    "name": field.name,
                                    "label": field.label,
                                    "description": field.description or "",
                                    "order_position": field.order_position,
                                    "field_type": field.field_type,
                                    "required": field.required,
                                    "parent_field": field.parent_field,
                                    "field_unit": field.field_unit,
                                    "placeholder": field.placeholder,
                                    "allow_custom": field.allow_custom,
                                }

                            subcat_name = found_subcategory["name"]
                            if subcat_name not in subcategory_fields_map:
                                subcategory_fields_map[subcat_name] = {
                                    "subcategory": found_subcategory,
                                    "fields": [],
                                }

                            enum = get_field_enum(field.name)
                            subcategory_fields_map[subcat_name]["fields"].append(
                                {
                                    "id": str(field.id),
                                    "name": json_field_data["name"],
                                    "label": json_field_data["label"],
                                    "description": json_field_data.get("description", ""),
                                    "order_position": json_field_data.get("order_position", 0),
                                    "field_type": json_field_data.get("field_type", "text"),
                                    "options": enum.options() if enum else None,
                                    "parent_field": json_field_data.get("parent_field"),
                                    "field_unit": json_field_data.get("field_unit"),
                                    "placeholder": json_field_data.get("placeholder"),
                                    "required": bool(json_field_data.get("required", False)),
                                    "allow_custom": bool(
                                        json_field_data.get("allow_custom", False)
                                    ),
                                    "child_fields": [],
                                }
                            )

                        # Build subcategories output
                        for subcat_name, subcat_data in subcategory_fields_map.items():
                            subcategory = subcat_data["subcategory"]
                            subcategory_id = f"{category_id}_{subcat_name}"

                            subcategories_out.append(
                                {
                                    "id": subcategory_id,
                                    "name": subcategory["name"],
                                    "label": subcategory["label"],
                                    "description": subcategory.get("description", ""),
                                    "order_position": subcategory.get("order_position", 0),
                                    "fields": subcat_data["fields"],
                                }
                            )

                    else:
                        # No subcategories in JSON, create general subcategory
                        fields_out = []
                        for field in category_missing_fields:
                            json_field_data = {
                                "name": field.name,
                                "label": field.label,
                                "description": field.description or "",
                                "order_position": field.order_position,
                                "field_type": field.field_type,
                                "required": field.required,
                                "parent_field": field.parent_field,
                                "field_unit": field.field_unit,
                                "placeholder": field.placeholder,
                                "allow_custom": field.allow_custom,
                            }

                            enum = get_field_enum(field.name)
                            fields_out.append(
                                {
                                    "id": str(field.id),
                                    "name": json_field_data["name"],
                                    "label": json_field_data["label"],
                                    "description": json_field_data.get("description", ""),
                                    "order_position": json_field_data.get("order_position", 0),
                                    "field_type": json_field_data.get("field_type", "text"),
                                    "options": enum.options() if enum else None,
                                    "parent_field": json_field_data.get("parent_field"),
                                    "field_unit": json_field_data.get("field_unit"),
                                    "placeholder": json_field_data.get("placeholder"),
                                    "required": bool(json_field_data.get("required", False)),
                                    "allow_custom": bool(
                                        json_field_data.get("allow_custom", False)
                                    ),
                                    "child_fields": [],
                                }
                            )

                        subcategories_out = [
                            {
                                "id": f"{category_id}_general",
                                "name": "general",
                                "label": "General",
                                "description": "",
                                "order_position": 1,
                                "fields": fields_out,
                            }
                        ]

                    # Add category to output
                    categories_out.append(
                        {
                            "id": category_id,
                            "name": json_category["name"] if json_category else category.name,
                            "label": json_category["label"] if json_category else category.label,
                            "description": json_category.get("description", "")
                            if json_category
                            else category.description or "",
                            "order_position": json_category.get("order_position", 0)
                            if json_category
                            else category.order_position,
                            "step": json_category.get("step", 0)
                            if json_category
                            else category.step,
                            "picture_url": json_category.get("picture_url")
                            if json_category
                            else category.picture_url,
                            "subcategories": subcategories_out,
                        }
                    )

                response["missing_by_categories"] = categories_out
            else:
                raise FileNotFoundError("Updated form fields file not found")

        except Exception as e:
            # Log the exception for debugging
            print(f"Exception in questionnaire status: {e}")
            import traceback

            traceback.print_exc()

            # Fallback to existing logic for backward compatibility with subcategories
            categories = quest_service.get_questions_by_categories()
            missing_set = set(missing)
            categories_out: list[dict[str, Any]] = []

            for category in categories:
                collected_fields: list[dict[str, Any]] = []
                for f in category.fields:
                    # include the field itself if missing (treat any field name present)
                    if f.name in missing_set:
                        enum = get_field_enum(f.name)
                        collected_fields.append(
                            {
                                "id": str(getattr(f, "id", None)),
                                "name": f.name,
                                "label": f.label,
                                "description": f.description,
                                "order_position": f.order_position,
                                "field_type": f.field_type,
                                "options": enum.options() if enum else None,
                                "parent_field": f.parent_field,
                                "field_unit": f.field_unit,
                                "placeholder": f.placeholder,
                                "required": bool(getattr(f, "required", False)),
                                "allow_custom": bool(getattr(f, "allow_custom", False)),
                                "child_fields": [],
                            }
                        )

                    # include any missing child fields under this group
                    for cf in getattr(f, "child_fields", []) or []:
                        if cf.name in missing_set:
                            enum = get_field_enum(cf.name)
                            collected_fields.append(
                                {
                                    "id": str(getattr(cf, "id", None)),
                                    "name": cf.name,
                                    "label": cf.label,
                                    "description": cf.description,
                                    "order_position": cf.order_position,
                                    "field_type": cf.field_type,
                                    "options": enum.options() if enum else None,
                                    "parent_field": cf.parent_field,
                                    "field_unit": cf.field_unit,
                                    "placeholder": cf.placeholder,
                                    "required": bool(getattr(cf, "required", False)),
                                    "allow_custom": bool(getattr(cf, "allow_custom", False)),
                                    "child_fields": [],
                                }
                            )

                if collected_fields:
                    # Wrap fields in a general subcategory for consistency
                    categories_out.append(
                        {
                            "id": str(getattr(category, "id", None)),
                            "name": category.name,
                            "label": category.label,
                            "description": category.description,
                            "order_position": category.order_position,
                            "step": category.step,
                            "picture_url": category.picture_url,
                            "subcategories": [
                                {
                                    "id": f"{str(category.id)}_general",
                                    "name": "general",
                                    "label": "General",
                                    "description": "",
                                    "order_position": 1,
                                    "fields": collected_fields,
                                }
                            ],
                        }
                    )

            # Primary approach result
            response["missing_by_categories"] = categories_out

        # Fallback: if still empty, group using direct field lookups
        if not categories_out:
            field_rows = quest_service.get_fields_by_names(missing)
            by_cat: dict[str, dict[str, Any]] = {}
            for f in field_rows:
                cat = f.category
                if not cat:
                    continue
                if cat.name not in by_cat:
                    by_cat[cat.name] = {
                        "id": getattr(cat, "id", None),
                        "name": cat.name,
                        "label": cat.label,
                        "description": cat.description,
                        "order_position": cat.order_position,
                        "step": cat.step,
                        "picture_url": cat.picture_url,
                        "fields": [],
                    }
                enum = get_field_enum(f.name)
                by_cat[cat.name]["fields"].append(
                    {
                        "id": getattr(f, "id", None),
                        "name": f.name,
                        "label": f.label,
                        "description": f.description,
                        "order_position": f.order_position,
                        "field_type": f.field_type,
                        "options": enum.options() if enum else None,
                        "parent_field": f.parent_field,
                        "field_unit": f.field_unit,
                        "placeholder": f.placeholder,
                        "required": bool(getattr(f, "required", False)),
                        "allow_custom": bool(getattr(f, "allow_custom", False)),
                        "child_fields": [],
                    }
                )

            fallback = list(by_cat.values())

            # Second fallback: use static resources definition if DB has no field metadata
            if not fallback:
                try:
                    root = Path(__file__).resolve().parents[4]
                    form_json = root / "resources" / "form_fields.json"
                    data = json.loads(form_json.read_text(encoding="utf-8"))
                    missing_set = set(missing)
                    cats_out: list[dict[str, Any]] = []
                    for cat in data:
                        fields_out: list[dict[str, Any]] = []
                        for f in cat.get("fields", []):
                            # top-level
                            if f.get("name") in missing_set:
                                enum = get_field_enum(f.get("name"))
                                fields_out.append(
                                    {
                                        "id": None,
                                        "name": f.get("name"),
                                        "label": f.get("label"),
                                        "description": f.get("description", ""),
                                        "order_position": f.get("order_position", 0),
                                        "field_type": f.get("field_type"),
                                        "options": enum.options() if enum else None,
                                        "parent_field": f.get("parent_field"),
                                        "field_unit": f.get("field_unit"),
                                        "placeholder": f.get("placeholder"),
                                        "required": bool(f.get("required", False)),
                                        "allow_custom": bool(f.get("allow_custom", False)),
                                        "child_fields": [],
                                    }
                                )
                            # children
                            for cf in f.get("child_fields", []) or []:
                                if cf.get("name") in missing_set:
                                    enum = get_field_enum(cf.get("name"))
                                    fields_out.append(
                                        {
                                            "id": None,
                                            "name": cf.get("name"),
                                            "label": cf.get("label"),
                                            "description": cf.get("description", ""),
                                            "order_position": cf.get("order_position", 0),
                                            "field_type": cf.get("field_type"),
                                            "options": enum.options() if enum else None,
                                            "parent_field": cf.get("parent_field"),
                                            "field_unit": cf.get("field_unit"),
                                            "placeholder": cf.get("placeholder"),
                                            "required": bool(cf.get("required", False)),
                                            "allow_custom": bool(cf.get("allow_custom", False)),
                                            "child_fields": [],
                                        }
                                    )
                        if fields_out:
                            cats_out.append(
                                {
                                    "id": None,
                                    "name": cat.get("name"),
                                    "label": cat.get("label"),
                                    "description": cat.get("description", ""),
                                    "order_position": cat.get("order_position", 0),
                                    "step": cat.get("step", 0),
                                    "picture_url": cat.get("picture_url"),
                                    "fields": fields_out,
                                }
                            )
                    response["missing_by_categories"] = cats_out
                except Exception:
                    response["missing_by_categories"] = []
            else:
                # Before assigning, ensure deterministic IDs for JSON-only source
                # Compute UUIDv5 from stable name to keep IDs consistent without DB
                NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "ryvin-questionnaire")
                for cat in fallback:
                    if cat.get("id") is None:
                        cat["id"] = str(uuid.uuid5(NAMESPACE, f"category:{cat.get('name')}"))
                    for f in cat.get("fields", []):
                        if f.get("id") is None:
                            f["id"] = str(uuid.uuid5(NAMESPACE, f"field:{f.get('name')}"))
                response["missing_by_categories"] = fallback

        # Final normalization/hydration step:
        # - Ensure every category and field has an exact DB ID when available
        # - Ensure response is structured under subcategories
        # - Assign stable composite IDs for subcategories: "{category_id}_{subcategory_name}"
        cats_resp = response.get("missing_by_categories") or []
        if cats_resp:
            # Collect all field names present (from any nesting) for a single DB lookup
            all_field_names: list[str] = []
            for cat in cats_resp:
                # Fields might be directly under category (legacy fallback) or under subcategories
                for f in cat.get("fields", []) or []:
                    if f and f.get("name"):
                        all_field_names.append(f.get("name"))
                for sub in cat.get("subcategories", []) or []:
                    for f in sub.get("fields", []) or []:
                        if f and f.get("name"):
                            all_field_names.append(f.get("name"))

            unique_names = list(set(all_field_names))
            field_rows_all = quest_service.get_fields_by_names(unique_names) if unique_names else []
            field_id_map = {fr.name: (str(getattr(fr, "id", "")) or None) for fr in field_rows_all}

            # Build category id map from DB by category name
            cat_rows_all = quest_service.get_all_categories()
            cat_id_map = {cr.name: (str(getattr(cr, "id", "")) or None) for cr in cat_rows_all}

            NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "ryvin-questionnaire")

            for cat in cats_resp:
                # Category ID from DB or deterministic UUID
                if cat.get("id") is None:
                    cat["id"] = cat_id_map.get(cat.get("name")) or str(
                        uuid.uuid5(NAMESPACE, f"category:{cat.get('name')}")
                    )

                # Normalize: if "fields" exist directly on category, wrap into a general subcategory
                if cat.get("fields"):
                    general_fields = cat.pop("fields") or []
                    # Ensure subcategories list exists
                    cat.setdefault("subcategories", [])
                    # Create or merge a "general" subcategory
                    # If a general subcategory already exists, extend its fields
                    existing_general = None
                    for sub in cat["subcategories"]:
                        if sub.get("name") == "general":
                            existing_general = sub
                            break
                    if existing_general is None:
                        existing_general = {
                            "name": "general",
                            "label": "General",
                            "description": "",
                            "order_position": 1,
                            "fields": [],
                        }
                        cat["subcategories"].append(existing_general)
                    existing_general["fields"].extend(general_fields)

                # Ensure every subcategory has a stable composite ID and hydrate field IDs
                for sub in cat.get("subcategories", []) or []:
                    # Assign composite subcategory ID
                    subcat_name = sub.get("name") or "general"
                    sub["id"] = f"{cat['id']}_{subcat_name}"

                    # Hydrate each field's ID from DB when available; otherwise deterministic UUID
                    for f in sub.get("fields", []) or []:
                        if f.get("id") is None:
                            fname = f.get("name")
                            f["id"] = field_id_map.get(fname) or str(
                                uuid.uuid5(NAMESPACE, f"field:{fname}")
                            )

    return response


@router.put(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def update_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
    questionnaire_in: QuestionnaireUpdate,
) -> QuestionnaireInDB:
    """
    Update current user's questionnaire
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_or_create_questionnaire(current_user.id)
    quest = quest_service.update_questionnaire(quest, questionnaire_in)
    return quest


@router.post(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def create_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
    questionnaire_in: QuestionnaireCreate,
) -> QuestionnaireInDB:
    """
    Create new Questionnaire for the current user
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_questionnaire(current_user.id)
    if quest:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="User already has a Questionnaire"
        )
    quest = quest_service.create_questionnaire(current_user.id, questionnaire_in)
    return quest


@router.post(
    "/complete",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def complete_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
) -> Any:
    """
    Mark questionnaire as completed
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_questionnaire(current_user.id)
    if not quest:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
        )

    quest = quest_service.complete_questionnaire(quest)

    if not quest.is_complete():
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Questionnaire is incomplete. Missing field: {quest_service.get_missing_required_fields(quest)}",
        )

    return {
        "message": "Questionnaire completed successfully",
        "completed_at": quest.completed_at,
    }


@router.get(
    "/categories",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_questions_by_categories(session: SessionDep):
    """
    Get all questionnaire questions organized by categories and subcategories

    Returns categories with subcategories structure from form_fields_updated.json
    or falls back to database structure for backward compatibility.
    """
    try:
        # Try to load from updated form fields JSON with subcategories
        root = Path(__file__).resolve().parents[4]
        form_json = root / "resources" / "form_fields_updated.json"

        if form_json.exists():
            data = json.loads(form_json.read_text(encoding="utf-8"))

            # Process and enhance with field options from enums
            categories_out = []
            for category in data:
                # Process subcategories
                subcategories_out = []

                if category.get("subcategories"):
                    for subcategory in category.get("subcategories", []):
                        fields_out = []

                        for field in subcategory.get("fields", []):
                            enum = get_field_enum(field.get("name"))
                            field_enhanced = {
                                "id": None,  # Will be populated from DB if available
                                "name": field.get("name"),
                                "label": field.get("label"),
                                "description": field.get("description", ""),
                                "order_position": field.get("order_position", 0),
                                "field_type": field.get("field_type"),
                                "options": enum.options() if enum else None,
                                "parent_field": field.get("parent_field"),
                                "field_unit": field.get("field_unit"),
                                "placeholder": field.get("placeholder"),
                                "required": bool(field.get("required", False)),
                                "allow_custom": bool(field.get("allow_custom", False)),
                                "child_fields": [],
                            }
                            fields_out.append(field_enhanced)

                        if fields_out:
                            subcategories_out.append(
                                {
                                    "name": subcategory.get("name"),
                                    "label": subcategory.get("label"),
                                    "description": subcategory.get("description", ""),
                                    "order_position": subcategory.get("order_position", 0),
                                    "fields": fields_out,
                                }
                            )
                else:
                    # Handle legacy format without subcategories
                    fields_out = []
                    for field in category.get("fields", []):
                        enum = get_field_enum(field.get("name"))
                        field_enhanced = {
                            "id": None,
                            "name": field.get("name"),
                            "label": field.get("label"),
                            "description": field.get("description", ""),
                            "order_position": field.get("order_position", 0),
                            "field_type": field.get("field_type"),
                            "options": enum.options() if enum else None,
                            "parent_field": field.get("parent_field"),
                            "field_unit": field.get("field_unit"),
                            "placeholder": field.get("placeholder"),
                            "required": bool(field.get("required", False)),
                            "allow_custom": bool(field.get("allow_custom", False)),
                            "child_fields": [],
                        }
                        fields_out.append(field_enhanced)

                    if fields_out:
                        subcategories_out.append(
                            {
                                "name": "general",
                                "label": "General",
                                "description": "",
                                "order_position": 1,
                                "fields": fields_out,
                            }
                        )

                if subcategories_out:
                    categories_out.append(
                        {
                            "id": None,
                            "name": category.get("name"),
                            "label": category.get("label"),
                            "description": category.get("description", ""),
                            "order_position": category.get("order_position", 0),
                            "step": category.get("step", 0),
                            "picture_url": category.get("picture_url"),
                            "subcategories": subcategories_out,
                        }
                    )

            return categories_out

    except Exception:
        pass  # Fall back to database approach

    # Fallback: Use database service (legacy support)
    quest_service = QuestionnaireService(session)
    db_categories = quest_service.get_questions_by_categories()

    # Wrap database results in subcategories for consistency
    categories_with_subcategories = []
    for category in db_categories:
        # Convert to dict if it's a model instance
        if hasattr(category, "__dict__"):
            cat_dict = {
                "id": str(category.id) if category.id else None,
                "name": category.name,
                "label": category.label,
                "description": category.description,
                "order_position": category.order_position,
                "step": category.step,
                "picture_url": category.picture_url,
                "subcategories": [
                    {
                        "name": "general",
                        "label": "General",
                        "description": "",
                        "order_position": 1,
                        "fields": [
                            {
                                "id": str(field.id) if field.id else None,
                                "name": field.name,
                                "label": field.label,
                                "description": field.description,
                                "order_position": field.order_position,
                                "field_type": field.field_type,
                                "options": get_field_enum(field.name).options()
                                if get_field_enum(field.name)
                                else None,
                                "parent_field": field.parent_field,
                                "field_unit": field.field_unit,
                                "placeholder": field.placeholder,
                                "required": bool(field.required),
                                "allow_custom": bool(field.allow_custom),
                                "child_fields": [],
                            }
                            for field in getattr(category, "fields", [])
                        ],
                    }
                ]
                if getattr(category, "fields", None)
                else [],
            }
        else:
            cat_dict = category

        categories_with_subcategories.append(cat_dict)

    return categories_with_subcategories
