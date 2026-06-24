from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS

from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: UUID
    username: str

    @classmethod
    def fake_user(cls):
        return CurrentUser(id=uuid4(), username="fake_user")


class ListingWriteModel(BaseModel):
    title: str
    description: str
    ask_price_amount: float
    ask_price_currency: str = "USD"

    class Config:
        schema_extra = {
            "example": {
                "title": "Antique Wooden Chair",
                "description": "Needs some restoration.",
                "ask_price_amount": 50.0,
                "ask_price_currency": "USD"
            }
        }



class ListingPublishModel(BaseModel):
    id: UUID

    class Config:
        schema_extra = {
            "example": {
                "id": str(uuid5(NAMESPACE_DNS, "Antique Wooden Chair"))
            }
        }



class ListingReadModel(BaseModel):
    id: UUID
    title: str = ""
    description: str
    ask_price_amount: float
    ask_price_currency: str


class ListingIndexModel(BaseModel):
    data: list[ListingReadModel]
