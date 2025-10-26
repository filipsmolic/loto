from pydantic import BaseModel, constr, validator
from typing import List, Optional


class TicketIn(BaseModel):
    owner_id: constr(min_length=1, max_length=20)
    numbers: str  # CSV format

    @validator("numbers")
    def validate_numbers(cls, v):
        nums = [int(x.strip()) for x in v.split(",") if x.strip()]
        if len(nums) < 6 or len(nums) > 10:
            raise ValueError("You must pick 6 to 10 numbers")
        if len(set(nums)) != len(nums):
            raise ValueError("Duplicate numbers")
        if not all(1 <= n <= 45 for n in nums):
            raise ValueError("Numbers must be in range 1–45")
        return nums


class StoreResults(BaseModel):
    numbers: List[int]
