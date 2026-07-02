from dataclasses import dataclass
from typing import Optional

import pytest
from seedwork.domain.value_objects import GenericUUID

from modules.bidding.application.command.place_bid import (
    PlaceBidCommand,
    PlaceBidOutputBoundary,
    PlaceBidOutputDto,
)


class MockPlaceBidPresenter(PlaceBidOutputBoundary):
    """
    A test double (mock) for the presenter. 
    It captures the DTO output from the application layer to verify the use case logic.
    """
    def __init__(self):
        self.presented_dto: Optional[PlaceBidOutputDto] = None

    def present(self, output_dto: PlaceBidOutputDto) -> None:
        self.presented_dto = output_dto


@pytest.mark.asyncio
async def test_place_bid_emits_output_dto(app):
    # Setup test data
    seller_id = GenericUUID.next_id()
    bidder_id = GenericUUID.next_id()
    listing_id = GenericUUID.next_id()

    # Create a mock presenter
    mock_presenter = MockPlaceBidPresenter()

    # Pre-seed the repository with a listing
    from modules.bidding.domain.entities import Listing
    from modules.bidding.domain.value_objects import Seller, Money
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    listing = Listing(
        id=listing_id,
        seller=Seller(id=seller_id),
        ask_price=Money(10),
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
    )
    
    with app.transaction_context() as ctx:
        # inject the listing into the repository directly
        from modules.bidding.domain.repositories import ListingRepository
        repo = ctx[ListingRepository]
        repo.add(listing)

    # Execute the command with the presenter
    command = PlaceBidCommand(
        listing_id=listing_id,
        bidder_id=bidder_id,
        amount=15,
    )
    
    async with app.transaction_context() as ctx:
        # Inject the mock presenter so the use case uses it instead of a real API presenter
        ctx.set_dependency("presenter", mock_presenter)
        await ctx.execute_async(command)

    # Assert the presenter received the correct output
    assert mock_presenter.presented_dto is not None
    assert mock_presenter.presented_dto.is_winner is True
    # With only 1 bid, current_price equals ask_price (auction-style second-price logic)
    assert mock_presenter.presented_dto.current_price.amount == 10


from modules.bidding.application.query.get_bidding_details import GetBiddingDetails, GetBiddingDetailsOutputBoundary
from modules.bidding.application.query.model_mappers import ListingDAO

class MockGetBiddingDetailsPresenter(GetBiddingDetailsOutputBoundary):
    def __init__(self):
        self.presented_dto: Optional[ListingDAO] = None

    def present(self, output_dto: ListingDAO) -> None:
        self.presented_dto = output_dto


@pytest.mark.asyncio
async def test_get_bidding_details_emits_output_dto(app):
    seller_id = GenericUUID.next_id()
    listing_id = GenericUUID.next_id()

    mock_presenter = MockGetBiddingDetailsPresenter()

    from modules.bidding.domain.entities import Listing
    from modules.bidding.domain.value_objects import Seller, Money
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    listing = Listing(
        id=listing_id,
        seller=Seller(id=seller_id),
        ask_price=Money(10),
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
    )
    
    with app.transaction_context() as ctx:
        from modules.bidding.domain.repositories import ListingRepository
        repo = ctx[ListingRepository]
        repo.add(listing)

    query = GetBiddingDetails(listing_id=listing_id)
    
    async with app.transaction_context() as ctx:
        ctx.set_dependency("presenter", mock_presenter)
        await ctx.execute_async(query)

    assert mock_presenter.presented_dto is not None
    assert mock_presenter.presented_dto.id == listing_id
    assert len(mock_presenter.presented_dto.bids) == 0
