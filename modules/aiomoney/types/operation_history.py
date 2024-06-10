from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, Field


class Operation(BaseModel):
    """
    Описание платежной операции
    https://yoomoney.ru/docs/wallet/user-account/operation-history#response-operation
    """
    operation_id: str
    status: str
    execution_datetime: datetime = Field(alias="datetime")
    title: str
    pattern_id: Union[str, None]
    direction: Union[Literal["in"], Literal["out"]]
    amount: int
    label: Union[str, None]
    operation_type: str = Field(alias="type")
