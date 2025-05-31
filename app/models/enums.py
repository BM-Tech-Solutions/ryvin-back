from enum import Enum, IntEnum

class Gender(str, Enum):
    MALE = "homme"
    FEMALE = "femme"

class RelationshipType(str, Enum):
    MARRIAGE = "mariage"
    SERIOUS_RELATIONSHIP = "relation_serieuse"

class SubscriptionType(str, Enum):
    FREE = "gratuit"
    PREMIUM = "premium"

class JourneyStep(IntEnum):
    PRE_COMPATIBILITY = 1
    VOICE_VIDEO_CALL = 2
    PHOTOS_UNLOCKED = 3
    PHYSICAL_MEETING = 4
    MEETING_FEEDBACK = 5

class MatchStatus(str, Enum):
    PENDING = "en_attente"
    ACTIVE = "actif"
    PAUSED = "pause"
    ENDED = "termine"

class PracticeLevel(str, Enum):
    NOT_PRACTICING = "non_pratiquant"
    OCCASIONALLY = "occasionnellement"
    REGULARLY = "regulierement"
    STRICTLY = "strictement"

class ImportanceLevel(str, Enum):
    NOT_IMPORTANT = "pas_important"
    SOMEWHAT_IMPORTANT = "peu_important"
    IMPORTANT = "important"
    VERY_IMPORTANT = "tres_important"
    ESSENTIAL = "essentiel"

class SportFrequency(str, Enum):
    NEVER = "jamais"
    RARELY = "rarement"
    OCCASIONALLY = "occasionnellement"
    REGULARLY = "regulierement"
    DAILY = "quotidiennement"

class DietType(str, Enum):
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarien"
    VEGAN = "vegan"
    PESCATARIAN = "pescetarien"
    HALAL = "halal"
    KOSHER = "casher"
    OTHER = "autre"

class HygieneImportance(str, Enum):
    RELAXED = "detendu"
    NORMAL = "normal"
    CAREFUL = "soigneux"
    VERY_CAREFUL = "tres_soigneux"

class ConsumptionLevel(str, Enum):
    NEVER = "jamais"
    RARELY = "rarement"
    OCCASIONALLY = "occasionnellement"
    REGULARLY = "regulierement"
    DAILY = "quotidiennement"

class StyleType(str, Enum):
    CASUAL = "decontracte"
    CLASSIC = "classique"
    ELEGANT = "elegant"
    SPORTY = "sportif"
    TRENDY = "tendance"
    ALTERNATIVE = "alternatif"
    OTHER = "autre"

class EducationLevel(str, Enum):
    PRIMARY = "primaire"
    SECONDARY = "secondaire"
    HIGH_SCHOOL = "lycee"
    ASSOCIATE = "bac_plus_2"
    BACHELOR = "licence"
    MASTER = "master"
    DOCTORATE = "doctorat"
    OTHER = "autre"

class EducationPreference(str, Enum):
    ANY = "indifferent"
    SIMILAR = "similaire"
    HIGHER = "superieur"
    LOWER = "inferieur"

class PersonalityType(str, Enum):
    INTROVERT = "introverti"
    AMBIVERT = "ambivert"
    EXTROVERT = "extraverti"

class LoveLanguage(str, Enum):
    WORDS_OF_AFFIRMATION = "mots_d_affirmation"
    QUALITY_TIME = "temps_de_qualite"
    RECEIVING_GIFTS = "cadeaux"
    ACTS_OF_SERVICE = "services_rendus"
    PHYSICAL_TOUCH = "contact_physique"

class SocialFrequency(str, Enum):
    RARELY = "rarement"
    MONTHLY = "mensuellement"
    WEEKLY = "hebdomadairement"
    SEVERAL_TIMES_WEEK = "plusieurs_fois_semaine"
    DAILY = "quotidiennement"

class SocialTolerance(str, Enum):
    VERY_LOW = "tres_faible"
    LOW = "faible"
    MODERATE = "moderee"
    HIGH = "elevee"
    VERY_HIGH = "tres_elevee"

class IntimacyFrequency(str, Enum):
    RARELY = "rarement"
    MONTHLY = "mensuellement"
    WEEKLY = "hebdomadairement"
    SEVERAL_TIMES_WEEK = "plusieurs_fois_semaine"
    DAILY = "quotidiennement"
    MULTIPLE_DAILY = "plusieurs_fois_jour"

class ComfortLevel(str, Enum):
    VERY_UNCOMFORTABLE = "tres_inconfortable"
    UNCOMFORTABLE = "inconfortable"
    NEUTRAL = "neutre"
    COMFORTABLE = "confortable"
    VERY_COMFORTABLE = "tres_confortable"

class PublicAffectionLevel(str, Enum):
    NONE = "aucune"
    MINIMAL = "minimale"
    MODERATE = "moderee"
    EXPRESSIVE = "expressive"
    VERY_EXPRESSIVE = "tres_expressive"

class CompatibilityType(str, Enum):
    COMPLEMENTARY = "complementaire"
    SIMILAR = "similaire"
    BALANCED = "equilibre"

class ProfessionalStatus(str, Enum):
    STUDENT = "etudiant"
    EMPLOYED = "employe"
    SELF_EMPLOYED = "independant"
    UNEMPLOYED = "sans_emploi"
    RETIRED = "retraite"
    OTHER = "autre"

class MessageType(str, Enum):
    TEXT = "texte"
    VOICE_CALL_REQUEST = "demande_appel_vocal"
    VIDEO_CALL_REQUEST = "demande_appel_video"

class MeetingStatus(str, Enum):
    PROPOSED = "proposee"
    ACCEPTED = "acceptee"
    REJECTED = "refusee"
    COMPLETED = "terminee"
    CANCELLED = "annulee"
