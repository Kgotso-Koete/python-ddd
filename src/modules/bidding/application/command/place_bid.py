from dataclasses import dataclass

from modules.bidding.application import bidding_module
from modules.bidding.domain.repositories import ListingRepository
from modules.bidding.domain.value_objects import Bid, Bidder, Money
from seedwork.application.commands import Command
from seedwork.domain.value_objects import GenericUUID


import abc

class PlaceBidCommand(Command):
    listing_id: GenericUUID
    bidder_id: GenericUUID
    amount: int  # todo: Decimal
    currency: str = "USD"


@dataclass
class PlaceBidOutputDto:
    is_winner: bool
    current_price: Money


class PlaceBidOutputBoundary(abc.ABC):
    @abc.abstractmethod
    def present(self, output_dto: PlaceBidOutputDto) -> None:
        pass


@bidding_module.handler(PlaceBidCommand)
async def place_bid(
    command: PlaceBidCommand, 
    listing_repository: ListingRepository,
    presenter: PlaceBidOutputBoundary
):
    bidder = Bidder(id=command.bidder_id)
    bid = Bid(bidder=bidder, max_price=Money(command.amount))

    listing = listing_repository.get_by_id(command.listing_id)
    listing.place_bid(bid)
    
    is_winner = listing.highest_bid is not None and listing.highest_bid.bidder.id == command.bidder_id
    output_dto = PlaceBidOutputDto(is_winner=is_winner, current_price=listing.current_price)
    presenter.present(output_dto)
