from typing import Annotated

from fastapi import APIRouter, Depends
from seedwork.foundation import Application

from api.dependencies import get_application
from api.models.bidding import BiddingResponse, PlaceBidRequest, PlaceBidResponse
from config.container import inject
from modules.bidding.application.command import PlaceBidCommand, RetractBidCommand
from modules.bidding.application.command.place_bid import PlaceBidOutputBoundary, PlaceBidOutputDto
from modules.bidding.application.query.get_bidding_details import (
    GetBiddingDetails,
    GetBiddingDetailsOutputBoundary
)
from modules.bidding.application.query.model_mappers import ListingDAO
from seedwork.foundation import TransactionContext
from api.dependencies import get_transaction_context

router = APIRouter()

"""
Inspired by https://developer.ebay.com/api-docs/buy/offer/types/api:Bidding
"""


class ApiGetBiddingDetailsPresenter(GetBiddingDetailsOutputBoundary):
    def __init__(self):
        self.response = None

    def present(self, output_dto: ListingDAO) -> None:
        mapped_bids = []
        for bid in output_dto.bids:
            mapped_bids.append({
                "amount": bid["max_price"]["amount"],
                "currency": bid["max_price"]["currency"],
                "bidder_id": bid["bidder_id"],
                "bidder_username": "Unknown",
            })

        self.response = BiddingResponse(
            listing_id=output_dto.id,
            auction_end_date=output_dto.ends_at,
            bids=mapped_bids,
        )


@router.get("/bidding/{listing_id}", tags=["bidding"], response_model=BiddingResponse)
async def get_bidding_details_of_listing(
    listing_id, 
    ctx: TransactionContext = Depends(get_transaction_context)
):
    """
    Shows listing details
    """
    query = GetBiddingDetails(listing_id=listing_id)
    presenter = ApiGetBiddingDetailsPresenter()
    ctx.set_dependency("presenter", presenter)
    
    await ctx.execute_async(query)
    
    return presenter.response


class ApiPlaceBidPresenter(PlaceBidOutputBoundary):
    def __init__(self):
        self.response = None
        
    def present(self, output_dto: PlaceBidOutputDto) -> None:
        self.response = PlaceBidResponse(
            is_winning=output_dto.is_winner,
            current_price=output_dto.current_price.amount
        )


@router.post(
    "/bidding/{listing_id}/place_bid", tags=["bidding"], response_model=PlaceBidResponse
)
@inject
async def place_bid(
    listing_id,
    request_body: PlaceBidRequest,
    app: Annotated[Application, Depends(get_application)],
):
    """
    Places a bid on a listing and returns whether the bid is currently winning.
    """
    from seedwork.domain.value_objects import GenericUUID
    
    presenter = ApiPlaceBidPresenter()
    
    async with app.transaction_context() as ctx:
        ctx.set_dependency("presenter", presenter)
        
        command = PlaceBidCommand(
            listing_id=GenericUUID(str(listing_id)),
            bidder_id=GenericUUID(str(request_body.bidder_id)),
            amount=request_body.amount,
        )
        await ctx.execute_async(command)
        
    return presenter.response


@router.post(
    "/bidding/{listing_id}/retract_bid",
    tags=["bidding"],
    response_model=BiddingResponse,
)
async def retract_bid(
    listing_id, 
    ctx: TransactionContext = Depends(get_transaction_context)
):
    """
    Retracts a bid from a listing
    """
    command = RetractBidCommand(
        listing_id=listing_id,
        bidder_id="",
    )
    await ctx.execute_async(command)

    query = GetBiddingDetails(listing_id=listing_id)
    presenter = ApiGetBiddingDetailsPresenter()
    ctx.set_dependency("presenter", presenter)
    
    await ctx.execute_async(query)
    
    return presenter.response
