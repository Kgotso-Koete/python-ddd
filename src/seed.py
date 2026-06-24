import asyncio
import uuid
import logging

from config.api_config import ApiConfig
from config.container import ApplicationContainer
from modules.iam.application.services import IamService
from modules.catalog.application.command.create_listing_draft import CreateListingDraftCommand
from modules.catalog.application.command.publish_listing_draft import PublishListingDraftCommand
from modules.bidding.application.command.place_bid import PlaceBidCommand
from seedwork.domain.value_objects import Money
from seedwork.infrastructure.database import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, name)

async def seed_database():
    config = ApiConfig()
    container = ApplicationContainer(config=config)
    app = container.application()
    db_engine = container.db_engine()

    logger.info("Ensuring database tables are created...")
    Base.metadata.create_all(db_engine)

    # Deterministic UUIDs
    seller_id = generate_uuid("alice.seller@example.com")
    buyer_id = generate_uuid("bob.buyer@example.com")
    admin_id = generate_uuid("admin@example.com")
    staff_id = generate_uuid("staff@example.com")

    # IAM service is synchronous
    with app.transaction_context() as ctx:
        iam_service = ctx[IamService]
        
        users_to_create = [
            (seller_id, "alice.seller@example.com", "password123", "seller_token"),
            (buyer_id, "bob.buyer@example.com", "password123", "buyer_token"),
            (admin_id, "admin@example.com", "password123", "admin_token"),
            (staff_id, "staff@example.com", "password123", "staff_token"),
        ]

        for u_id, email, pwd, token in users_to_create:
            try:
                iam_service.create_user(
                    user_id=u_id,
                    email=email,
                    password=pwd,
                    access_token=token,
                )
                logger.info(f"Created user: {email}")
            except ValueError:
                logger.info(f"User {email} already exists")
            except Exception as e:
                logger.warning(f"Error creating user {email}: {e}")

    listings = [
        {
            "id": generate_uuid("Vintage Leather Jacket"),
            "title": "Vintage Leather Jacket",
            "desc": "Authentic 1980s leather jacket in excellent condition.",
            "price": 150,
            "seller_id": seller_id,
            "publish": True,
        },
        {
            "id": generate_uuid("Professional DSLR Camera"),
            "title": "Professional DSLR Camera",
            "desc": "Used for 2 years, comes with 2 lenses.",
            "price": 800,
            "seller_id": admin_id,
            "publish": True,
        },
        {
            "id": generate_uuid("Antique Wooden Chair"),
            "title": "Antique Wooden Chair",
            "desc": "Needs some restoration.",
            "price": 50,
            "seller_id": seller_id,
            "publish": False,
        }
    ]

    for item in listings:
        try:
            cmd = CreateListingDraftCommand(
                listing_id=item["id"],
                title=item["title"],
                description=item["desc"],
                ask_price=Money(item["price"], "USD"),
                seller_id=item["seller_id"]
            )
            await app.execute_async(cmd)
            logger.info(f"Created listing draft: {item['title']}")
        except Exception as e:
            logger.info(f"Listing draft {item['title']} already exists or failed. ({type(e).__name__})")
            
        if item["publish"]:
            try:
                publish_cmd = PublishListingDraftCommand(
                    listing_id=item["id"],
                    seller_id=item["seller_id"]
                )
                await app.execute_async(publish_cmd)
                logger.info(f"Published listing: {item['title']}")
            except Exception as e:
                logger.info(f"Listing {item['title']} already published or failed. ({type(e).__name__})")

    # Place bids
    bids = [
        {
            "listing_id": generate_uuid("Vintage Leather Jacket"),
            "bidder_id": buyer_id,
            "amount": 160
        },
        {
            "listing_id": generate_uuid("Vintage Leather Jacket"),
            "bidder_id": staff_id,
            "amount": 180
        },
        {
            "listing_id": generate_uuid("Professional DSLR Camera"),
            "bidder_id": buyer_id,
            "amount": 850
        }
    ]

    for bid in bids:
        try:
            place_bid_cmd = PlaceBidCommand(
                listing_id=bid["listing_id"],
                bidder_id=bid["bidder_id"],
                amount=bid["amount"]
            )
            await app.execute_async(place_bid_cmd)
            logger.info(f"Placed bid of {bid['amount']} on listing {bid['listing_id']} by bidder {bid['bidder_id']}")
        except Exception as e:
            logger.info(f"Bid already placed or couldn't be placed: {e} ({type(e).__name__})")

if __name__ == "__main__":
    asyncio.run(seed_database())
