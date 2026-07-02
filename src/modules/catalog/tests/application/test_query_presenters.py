from dataclasses import dataclass
from typing import Optional

import pytest
from seedwork.domain.value_objects import GenericUUID

from modules.catalog.application.query.get_listing_details import (
    GetListingDetails,
    GetListingDetailsOutputBoundary,
)
from modules.catalog.application.query.get_all_listings import (
    GetAllListings,
    GetAllListingsOutputBoundary,
)


class MockGetListingDetailsPresenter(GetListingDetailsOutputBoundary):
    def __init__(self):
        self.presented_dto: Optional[dict] = None

    def present(self, output_dto: dict) -> None:
        self.presented_dto = output_dto


class MockGetAllListingsPresenter(GetAllListingsOutputBoundary):
    def __init__(self):
        self.presented_dto: Optional[list[dict]] = None

    def present(self, output_dto: list[dict]) -> None:
        self.presented_dto = output_dto


@pytest.mark.asyncio
async def test_get_listing_details_emits_output_dto(app):
    seller_id = GenericUUID.next_id()
    listing_id = GenericUUID.next_id()

    mock_presenter = MockGetListingDetailsPresenter()

    # Pre-seed the catalog repository with a listing
    from modules.catalog.domain.entities import Listing
    from seedwork.domain.value_objects import Money
    
    listing = Listing(
        id=listing_id,
        title="Test Listing",
        description="A test description",
        ask_price=Money(10),
        seller_id=seller_id,
    )
    
    with app.transaction_context() as ctx:
        from modules.catalog.domain.repositories import ListingRepository
        repo = ctx[ListingRepository]
        repo.add(listing)

    query = GetListingDetails(listing_id=listing_id)
    
    async with app.transaction_context() as ctx:
        ctx.set_dependency("presenter", mock_presenter)
        await ctx.execute_async(query)

    assert mock_presenter.presented_dto is not None
    assert mock_presenter.presented_dto["id"] == listing_id
    assert mock_presenter.presented_dto["title"] == "Test Listing"


@pytest.mark.asyncio
async def test_get_all_listings_emits_output_dto(app):
    seller_id = GenericUUID.next_id()
    listing_id = GenericUUID.next_id()

    mock_presenter = MockGetAllListingsPresenter()

    from modules.catalog.domain.entities import Listing
    from seedwork.domain.value_objects import Money
    
    listing = Listing(
        id=listing_id,
        title="Test Listing",
        description="A test description",
        ask_price=Money(10),
        seller_id=seller_id,
    )
    
    with app.transaction_context() as ctx:
        from modules.catalog.domain.repositories import ListingRepository
        repo = ctx[ListingRepository]
        repo.add(listing)

    query = GetAllListings()
    
    async with app.transaction_context() as ctx:
        ctx.set_dependency("presenter", mock_presenter)
        await ctx.execute_async(query)

    assert mock_presenter.presented_dto is not None
    assert len(mock_presenter.presented_dto) == 1
    assert mock_presenter.presented_dto[0]["id"] == listing_id
