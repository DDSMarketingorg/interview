from pydantic import BaseModel

class GHLContact(BaseModel):
    id: str
    firstName: str
    phone: str
    email: str
    practiceName: str


class GHLContactRequest(BaseModel):
    event: str
    contact: GHLContact


class GHLContactResponse(BaseModel):
    contact_status: str
    contact_id: str
