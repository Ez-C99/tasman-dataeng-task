from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dq_enforce: bool = Field(
        default=True,
        validation_alias="DQ_ENFORCE",
    )
