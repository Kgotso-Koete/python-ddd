import abc
from dataclasses import dataclass

from sqlalchemy.orm import Session

from modules.catalog.application import catalog_module
from modules.catalog.application.query.model_mappers import map_listing_model_to_dao
from modules.catalog.infrastructure.listing_repository import ListingModel
from seedwork.application.queries import Query
from seedwork.application.query_handlers import QueryResult
from seedwork.domain.value_objects import GenericUUID


class GetListingDetailsOutputBoundary(abc.ABC):
    @abc.abstractmethod
    def present(self, output_dto: dict) -> None:
        pass


class GetListingDetails(Query):
    listing_id: GenericUUID


@catalog_module.handler(GetListingDetails)
def get_listing_details(
    query: GetListingDetails, 
    session: Session,
    presenter: GetListingDetailsOutputBoundary
) -> None:
    row = session.query(ListingModel).filter_by(id=query.listing_id).one()
    details = map_listing_model_to_dao(row)
    presenter.present(details)
