from pydantic import BaseModel, Field


class ParentSummary(BaseModel):
    parent_id: int = Field(alias="parentId")
    nickname: str | None
    profile_count: int = Field(alias="profileCount")
    provider: str | None = None

    model_config = {"populate_by_name": True}
