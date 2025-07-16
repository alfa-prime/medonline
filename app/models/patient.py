from typing import Optional

from pydantic import BaseModel, Field, constr


class PatientSearchRequest(BaseModel):
    last_name: str = Field(...)
    first_name: str = Field(...)
    middle_name: Optional[str] = Field(None)
    birthday: constr(pattern=r"\d{2}\.\d{2}\.\d{4}") = Field(...)