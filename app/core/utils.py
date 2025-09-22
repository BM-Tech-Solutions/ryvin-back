from typing import Generic, TypeVar

from fastapi import Request
from furl import furl
from pydantic import BaseModel
from sqlalchemy.orm import Query

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    next: str | None = None
    previous: str | None = None
    total_items: int
    nbr_items: int
    page: int
    total_pages: int


def paginate(query: Query, page: int, per_page: int, request: Request) -> Page[T]:
    # Get total item count
    total_items = query.count()

    # Calculate pagination metrics
    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Fetch the items for the current page
    items = query.limit(per_page).offset(offset).all()

    # Generate next and previous page links
    url_obj = furl(str(request.url))

    next_link = None
    if page < total_pages:
        url_obj.args["page"] = page + 1
        next_link = url_obj.url

    previous_link = None
    if page > 1:
        url_obj.args["page"] = page - 1
        previous_link = url_obj.url

    return Page(
        items=items,
        next=next_link,
        previous=previous_link,
        total_items=total_items,
        nbr_items=len(items),
        page=page,
        total_pages=total_pages,
    )
