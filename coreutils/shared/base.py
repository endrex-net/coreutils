from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DTO(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
        frozen=True,
    )
