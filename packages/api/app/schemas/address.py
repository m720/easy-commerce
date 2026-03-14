from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class AddressBase(BaseModel):
    label: Optional[str] = None
    street: str
    city: str
    state: Optional[str] = None
    country: str
    postal_code: str
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    is_default: Optional[bool] = None


class AddressResponse(AddressBase):
    model_config = {"from_attributes": True}
    id: UUID
    user_id: UUID
