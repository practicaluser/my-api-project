from pydantic import BaseModel, ConfigDict


# 게시물 생성을 위한 기본 스키마
class PostBase(BaseModel):
    title: str
    content: str


# 게시물 생성을 위한 요청 스키마 (PostBase 상속)
class PostCreate(PostBase):
    pass


# 게시물 조회를 위한 응답 스키마 (PostBase 상속)
class Post(PostBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
