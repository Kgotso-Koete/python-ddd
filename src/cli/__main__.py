import uuid
import asyncio

from config.container import ApplicationContainer
from modules.catalog.application.command import CreateListingDraftCommand
from modules.catalog.application.query.get_all_listings import (
    GetAllListings,
    GetAllListingsOutputBoundary
)
from modules.catalog.domain.repositories import ListingRepository
from modules.catalog.infrastructure.listing_repository import Base
from seedwork.domain.value_objects import Money
from seedwork.infrastructure.logging import LoggerFactory, logger

class CliGetAllListingsPresenter(GetAllListingsOutputBoundary):
    def __init__(self):
        self.response = None
    def present(self, output_dto: list[dict]) -> None:
        self.response = output_dto

from config.api_config import ApiConfig

async def main():
    LoggerFactory.configure(logger_name="cli")

    config = ApiConfig()
    config.DATABASE_ECHO = False
    config.DEBUG = True
    
    container = ApplicationContainer(config=config)

    engine = container.db_engine()
    Base.metadata.create_all(engine)

    app = container.application()

    print("\n--- Testing Commands via CLI ---")
    async with app.transaction_context() as ctx:
        await ctx.execute_async(
            CreateListingDraftCommand(
                listing_id=uuid.uuid4(),
                title="First listing from CLI",
                description="This is a test from the command line",
                ask_price=Money(100),
                seller_id=uuid.UUID(int=1),
            )
        )
        print("✅ Created listing draft successfully!")

    print("\n--- Testing Queries via CLI ---")
    async with app.transaction_context() as ctx:
        presenter = CliGetAllListingsPresenter()
        ctx.set_dependency("presenter", presenter)
        await ctx.execute_async(GetAllListings())
        
        listings = presenter.response
        print(f"Found {len(listings)} Listings:")
        for listing in listings:
            print(f"  - [{listing['id']}] {listing['title']} (Asking: {listing['ask_price_amount']} {listing['ask_price_currency']})")

    async with app.transaction_context() as ctx:
        listing_repository = ctx[ListingRepository]
        listing_count = listing_repository.count()
        logger.info(f"There are {listing_count} listings in the database")

if __name__ == "__main__":
    asyncio.run(main())
