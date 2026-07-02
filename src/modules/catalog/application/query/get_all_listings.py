import abc
from sqlalchemy.orm import Session

from modules.catalog.application import catalog_module
from modules.catalog.application.query.model_mappers import map_listing_model_to_dao
from modules.catalog.infrastructure.listing_repository import ListingModel
from seedwork.application.queries import Query


class GetAllListingsOutputBoundary(abc.ABC):
    @abc.abstractmethod
    def present(self, output_dto: list[dict]) -> None:
        pass


class GetAllListings(Query):
    """This query does not need any parameters"""


@catalog_module.handler(GetAllListings)
async def get_all_listings(
    query: GetAllListings,
    session: Session,
    presenter: GetAllListingsOutputBoundary
) -> None:
    queryset = session.query(ListingModel)
    listings = [map_listing_model_to_dao(row) for row in queryset.all()]
    presenter.present(listings)
