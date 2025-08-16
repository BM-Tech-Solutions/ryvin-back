import uuid
from typing import Any
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.models.enums import get_field_enum
from app.schemas.questionnaire import (
    CategoryOut,
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
            "missing_by_categories": list[dict]
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

    # When incomplete, also group missing fields by their categories with full metadata
    if not is_completed:
        # Use service that attaches child_fields to field groups
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

                # include any missing child fields under this group
                for cf in getattr(f, "child_fields", []) or []:
                    if cf.name in missing_set:
                        enum = get_field_enum(cf.name)
                        collected_fields.append(
                            {
                                "id": getattr(cf, "id", None),
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
                categories_out.append(
                    {
                        "id": getattr(category, "id", None),
                        "name": category.name,
                        "label": category.label,
                        "description": category.description,
                        "order_position": category.order_position,
                        "step": category.step,
                        "picture_url": category.picture_url,
                        "fields": collected_fields,
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

        # Final hydration step: if any ids are None, try to fill them from DB by name
        cats_resp = response.get("missing_by_categories") or []
        if cats_resp:
            # Build field id map from DB for all field names present
            all_field_names: list[str] = []
            for cat in cats_resp:
                for f in cat.get("fields", []):
                    all_field_names.append(f.get("name"))
            unique_names = list(set(all_field_names))
            field_rows_all = quest_service.get_fields_by_names(unique_names)
            field_id_map = {fr.name: (str(getattr(fr, "id", "")) or None) for fr in field_rows_all}
            # Build category id map from DB by category name
            cat_rows_all = quest_service.get_all_categories()
            cat_id_map = {cr.name: (str(getattr(cr, "id", "")) or None) for cr in cat_rows_all}

            # Minimal debug prints in server logs to help diagnose if needed
            if not field_id_map:
                print("[questionnaire_status] hydration: no field ids found for names:", unique_names)
            if not cat_id_map:
                print("[questionnaire_status] hydration: no category ids available in DB")

            NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "ryvin-questionnaire")
            for cat in cats_resp:
                if cat.get("id") is None:
                    cat["id"] = cat_id_map.get(cat.get("name")) or str(
                        uuid.uuid5(NAMESPACE, f"category:{cat.get('name')}")
                    )
                for f in cat.get("fields", []):
                    if f.get("id") is None:
                        f["id"] = field_id_map.get(f.get("name")) or str(
                            uuid.uuid5(NAMESPACE, f"field:{f.get('name')}")
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
    response_model=list[CategoryOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_questions_by_categories(session: SessionDep):
    """
    Get all questionnaire questions organized by categories from the database
    """
    quest_service = QuestionnaireService(session)
    return quest_service.get_questions_by_categories()
