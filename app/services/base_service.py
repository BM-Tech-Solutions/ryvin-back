from sqlalchemy.orm import Session


class BaseService:
    """
    Base service class with common database operations
    """

    def __init__(self, session: Session):
        self.session = session

    def commit_changes(self):
        """
        Commit changes to the database
        """
        self.session.commit()

    def rollback_changes(self):
        """
        Rollback changes
        """
        self.session.rollback()
