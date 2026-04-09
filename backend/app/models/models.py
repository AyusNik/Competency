from pydantic import BaseModel, Field
from typing import Optional, List
from bson import ObjectId


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, *args):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


class CompetencyModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    description: Optional[str] = None
    promotion_from: Optional[str] = None
    promotion_to: Optional[str] = None
    order: Optional[int] = 0

    class Config:
        populate_by_name = True


class CompetencyUnitModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    competency_id: str
    description: Optional[str] = None

    class Config:
        populate_by_name = True


class CourseModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    code: str
    description: Optional[str] = None

    class Config:
        populate_by_name = True


class RequirementItem(BaseModel):
    courses: List[str] = []  # course names/ids
    min_requirements: int = 1


class TrainingGroup(BaseModel):
    group_name: str
    requirement_grouping: str = "And"  # And / Or
    items: List[RequirementItem] = []


class TrainingModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    description: Optional[str] = None
    basic_groups: List[TrainingGroup] = []
    advanced_groups: List[TrainingGroup] = []

    class Config:
        populate_by_name = True


class PLRModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    competency_element_id: str
    level: str  # A, B, C, D
    requirements: Optional[str] = None

    class Config:
        populate_by_name = True


class AssessmentItem(BaseModel):
    exams: List[str] = []
    min_requirements: int = 1


class AssessmentGroup(BaseModel):
    group_name: str
    requirement_grouping: str = "And"
    items: List[AssessmentItem] = []


class AssessmentModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str                        # e.g. "PLE", "CPA", "OJT"
    competency_element: str          # e.g. "DSA - Arrays"
    description: Optional[str] = None
    expert_groups: List[AssessmentGroup] = []
    advanced_groups: List[AssessmentGroup] = []
    release_date: Optional[str] = None  # ISO date "YYYY-MM-DD"; if set, locked until this date

    class Config:
        populate_by_name = True


class ContentMappingModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    ce_unit: str
    competency_element: str
    plr_table: str
    training_ids: List[str] = []
    assessment_ids: List[str] = []   # real ObjectIds of AssessmentModel docs
    assessment_types: List[str] = [] # display labels e.g. ["PLE", "CPA"]

    class Config:
        populate_by_name = True
