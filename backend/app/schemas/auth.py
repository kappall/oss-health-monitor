from pydantic import BaseModel

class Token(BaseModel):
    acces_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: int | None = None
    github_id: int | None = None

class GitHubUser(BaseModel):
    id: int
    login: str
    email: str | None = None
    name: str | None = None

class UserResponse(BaseModel):
    id: int
    github_id: int
    usermame: str
    email: str | None = None

    class Config:
        from_attributes = True