"""
Schemas for the REST APIs inputs and outputs
"""

# from fastapi_utils.enums import StrEnum
from pydantic import BaseModel, PositiveInt


class NewElevatorParams(BaseModel):
    """
    JSON used to create a new elevator
    """

    name: str
    floors: PositiveInt


class ElevatorResponse(BaseModel):
    """
    JSON describing the elevator in the body of the HTTP response
    """

    id: str
    name: str
    floors: PositiveInt
