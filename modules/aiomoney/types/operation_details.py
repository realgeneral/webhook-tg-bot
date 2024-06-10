from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, Field


class OperationDetails(BaseModel):
    """
    Детальная информация об операции из истории
    https://yoomoney.ru/docs/wallet/user-account/operation-details
    """
    error: Union[str, None]
    operation_id: str
    status: str
    pattern_id: Union[str, None]
    direction: Union[Literal["in"], Literal["out"]]
    amount: int
    amount_due: Union[int, None]
    fee: Union[int, None]
    operation_datetime: datetime = Field(alias="datetime")
    title: str
    sender: Union[int, None]
    recipient: Union[str, None]
    recipient_type: Union[str, None]
    message: Union[str, None]
    comment: Union[str, None]
    label: Union[str, None]
    details: Union[str, None]
    operation_type: str = Field(alias="type")
