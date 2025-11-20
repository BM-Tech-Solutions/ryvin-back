from sqlalchemy.orm import Session


class BaseService:
    """
    Base service class with common database operations
    """

    def __init__(self, session: Session):
        self.session = session
