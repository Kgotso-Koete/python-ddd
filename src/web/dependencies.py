from typing import Annotated
from fastapi import Request, Depends
from seedwork.foundation import TransactionContext
from api.dependencies import get_transaction_context
from modules.iam.application.services import IamService
from modules.iam.domain.entities import User

class NotAuthenticatedException(Exception):
    """Raised when a user is required but not authenticated for a UI route."""
    pass

async def get_current_ui_user_optional(
    request: Request,
    ctx: Annotated[TransactionContext, Depends(get_transaction_context)]
) -> User | None:
    """
    Dependency for public UI routes that can optionally show user-specific data.
    Returns the User if the access_token cookie is valid, otherwise None.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
        
    current_user = ctx[IamService].find_user_by_access_token(access_token)
    return current_user

async def get_current_ui_user(
    current_user: Annotated[User | None, Depends(get_current_ui_user_optional)]
) -> User:
    """
    Dependency for protected UI routes.
    If the user is not authenticated, raises an exception which triggers a redirect to the login page.
    """
    if current_user is None:
        raise NotAuthenticatedException()
    return current_user
