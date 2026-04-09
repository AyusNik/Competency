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


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    job_title: Optional[str] = ""


class UserLogin(BaseModel):
    email: str
    password: str


class UserDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    email: str
    password_hash: str
    job_title: Optional[str] = ""

    class Config:
        populate_by_name = True


class UserCompetencyMapping(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str
    competency_ids: List[str] = []

    class Config:
        populate_by_name = True
