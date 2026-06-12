import asyncio
import uuid
from config.api_config import ApiConfig
from config.container import ApplicationContainer
from modules.iam.application.services import IamService
from modules.catalog.application.command.create_listing_draft import CreateListingDraftCommand
from modules.catalog.application.command.publish_listing_draft import PublishListingDraftCommand
from seedwork.domain.value_objects import Money

async def seed_database():
    config = ApiConfig()
    container = ApplicationContainer(config=config)
    app = container.application()

    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()

    # IAM service is synchronous
    with app.transaction_context() as ctx:
        iam_service = ctx[IamService]
        
        try:
            iam_service.create_user(
                user_id=user1_id,
                email="alice@example.com",
                password="password123",
                access_token="alice_token",
            )
            print("Created user: alice@example.com")
        except ValueError:
            print("User alice already exists")

        try:
            iam_service.create_user(
                user_id=user2_id,
                email="bob@example.com",
                password="password123",
                access_token="bob_token",
            )
            print("Created user: bob@example.com")
        except ValueError:
            print("User bob already exists")

    # Create listings for Alice
    listing1_id = uuid.uuid4()
    cmd1 = CreateListingDraftCommand(
        listing_id=listing1_id,
        title="Vintage Leather Jacket",
        description="Authentic 1980s leather jacket in excellent condition.",
        ask_price=Money(150, "USD"),
        seller_id=user1_id
    )
    await app.execute_async(cmd1)
    
    publish_cmd1 = PublishListingDraftCommand(
        listing_id=listing1_id,
        seller_id=user1_id
    )
    await app.execute_async(publish_cmd1)
    print("Created and published listing: Vintage Leather Jacket")

    # Create listings for Bob
    listing2_id = uuid.uuid4()
    cmd2 = CreateListingDraftCommand(
        listing_id=listing2_id,
        title="Professional DSLR Camera",
        description="Used for 2 years, comes with 2 lenses.",
        ask_price=Money(800, "USD"),
        seller_id=user2_id
    )
    await app.execute_async(cmd2)
    
    publish_cmd2 = PublishListingDraftCommand(
        listing_id=listing2_id,
        seller_id=user2_id
    )
    await app.execute_async(publish_cmd2)
    print("Created and published listing: Professional DSLR Camera")

if __name__ == "__main__":
    asyncio.run(seed_database())
