from typing import Annotated

from fastapi import APIRouter, Depends

from api.dependencies import Application, User, get_application, get_authenticated_user, get_transaction_context
from api.models.catalog import ListingIndexModel, ListingReadModel, ListingWriteModel
from config.container import inject
from modules.catalog.application.command import (
    CreateListingDraftCommand,
    DeleteListingDraftCommand,
    PublishListingDraftCommand,
)
from modules.catalog.application.query.get_all_listings import GetAllListings
from modules.catalog.application.query.get_listing_details import (
    GetListingDetails, 
    GetListingDetailsOutputBoundary
)
from seedwork.domain.value_objects import GenericUUID, Money
from seedwork.foundation import TransactionContext

"""
Inspired by https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/createOffer
"""

router = APIRouter()


class ApiGetListingDetailsPresenter(GetListingDetailsOutputBoundary):
    def __init__(self):
        self.response = None

    def present(self, output_dto: dict) -> None:
        self.response = ListingReadModel(**output_dto)


@router.get("/catalog", tags=["catalog"], response_model=ListingIndexModel)
async def get_all_listings(app: Annotated[Application, Depends(get_application)]):
    """
    Shows all published listings in the catalog
    """
    query = GetAllListings()
    result = await app.execute_async(query)
    return dict(data=result)


@router.get("/catalog/{listing_id}", tags=["catalog"], response_model=ListingReadModel)
async def get_listing_details(
    listing_id, 
    ctx: TransactionContext = Depends(get_transaction_context)
):
    """
    Shows listing details
    """
    query = GetListingDetails(listing_id=listing_id)
    
    presenter = ApiGetListingDetailsPresenter()
    ctx.set_dependency("presenter", presenter)
    
    await ctx.execute_async(query)
    return presenter.response


@router.post(
    "/catalog", tags=["catalog"], status_code=201, response_model=ListingReadModel
)
async def create_listing(
    request_body: ListingWriteModel,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    ctx: TransactionContext = Depends(get_transaction_context)
):
    """
    Creates a new listing
    """
    command = CreateListingDraftCommand(
        listing_id=GenericUUID.next_id(),
        title=request_body.title,
        description=request_body.description,
        ask_price=Money(request_body.ask_price_amount, request_body.ask_price_currency),
        seller_id=current_user.id,
    )
    await ctx.execute_async(command)

    query = GetListingDetails(listing_id=command.listing_id)
    presenter = ApiGetListingDetailsPresenter()
    ctx.set_dependency("presenter", presenter)
    
    await ctx.execute_async(query)
    return presenter.response


@router.delete(
    "/catalog/{listing_id}", tags=["catalog"], status_code=204, response_model=None
)
@inject
async def delete_listing(
    listing_id,
    app: Annotated[Application, Depends(get_application)],
    current_user: Annotated[User, Depends(get_authenticated_user)],
):
    """
    Deletes a listing
    """
    command = DeleteListingDraftCommand(
        listing_id=listing_id,
        seller_id=current_user.id,
    )
    await app.execute_async(command)


@router.post(
    "/catalog/{listing_id}/publish",
    tags=["catalog"],
    status_code=200,
    response_model=ListingReadModel,
)
async def publish_listing(
    listing_id: GenericUUID,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    ctx: TransactionContext = Depends(get_transaction_context)
):
    """
    Publishes a listing
    """
    command = PublishListingDraftCommand(
        listing_id=listing_id,
        seller_id=current_user.id,
    )
    await ctx.execute_async(command)

    query = GetListingDetails(listing_id=listing_id)
    presenter = ApiGetListingDetailsPresenter()
    ctx.set_dependency("presenter", presenter)
    
    await ctx.execute_async(query)
    return presenter.response
