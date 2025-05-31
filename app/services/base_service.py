from sqlalchemy.orm import Session


class BaseService:
    """
    Base service class with common database operations
    """
    def __init__(self, db: Session):
        self.db = db
    
    def commit_changes(self):
        """
        Commit changes to the database
        """
        self.db.commit()
    
    def rollback_changes(self):
        """
        Rollback changes
        """
        self.db.rollback()
