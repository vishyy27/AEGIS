from pydantic import BaseModel


class IntegrationBase(BaseModel):
    type: str  # 'github', 'gitlab', 'jenkins', 'azure', 'aws', 'kubernetes'


class IntegrationCreate(IntegrationBase):
    credentials: dict


class IntegrationResponse(IntegrationBase):
    id: int
    connected: bool

    class Config:
        from_attributes = True
