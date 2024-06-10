from pydantic import BaseModel, Field

from typing import Union, List, Any

class BalanceDetails(BaseModel):
    total: int
    available: int
    deposition_pending: Union[int, None]
    blocked: Union[int, None]
    debt: Union[int, None]
    hold: Union[int, None]


class LinkedCard(BaseModel):
    pan_fragment: str
    card_type: str = Field(None, alias="type")


class AccountInfo(BaseModel):
    """
    Получение информации о состоянии счета пользователя
    https://yoomoney.ru/docs/wallet/user-account/account-info
    """
    account: str  # номер счета
    balance: int  # баланс счета
    currency: str  # код валюты счета
    account_status: str
    account_type: str
    balance_details: Union[BalanceDetails, None]
    cards_linked: Union[Union[LinkedCard, Any], None]
