from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import Gender, RelationshipType, ProfessionalStatus, EducationLevel


class UserProfile(BaseModel):
    """
    User profile model containing personal information
    """
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True)
    prenom = Column(String, nullable=False)
    genre = Column(String, nullable=False)  # Using Gender enum values
    age = Column(Integer, nullable=False)
    ville = Column(String, nullable=False)
    nationalite = Column(String, nullable=False)
    langues = Column(JSONB, nullable=False, default=list)  # List of languages as JSON
    situation_professionnelle = Column(String, nullable=False)  # Using ProfessionalStatus enum values
    niveau_etudes = Column(String, nullable=False)  # Using EducationLevel enum values
    deja_marie = Column(Boolean, nullable=False)
    a_des_enfants = Column(Boolean, nullable=False)
    nombre_enfants = Column(Integer, nullable=True)
    type_relation_recherchee = Column(String, nullable=False)  # Using RelationshipType enum values
    genre_recherche = Column(String, nullable=False)  # Using Gender enum values
    photos = Column(JSONB, nullable=False, default=list)  # List of photo URLs as JSON
    is_profile_complete = Column(Boolean, default=False, nullable=False)
    profile_completion_step = Column(Integer, default=1, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile {self.id}: {self.prenom}, {self.age}>"
