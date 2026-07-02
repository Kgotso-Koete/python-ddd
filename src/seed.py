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
from sqlalchemy import text
from datetime import datetime, timedelta

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
    miles_id = generate_uuid("miles.morales@example.com")
    ororo_id = generate_uuid("ororo.munroe@example.com")
    matt_id = generate_uuid("matt.murdock@example.com")
    bruce_id = generate_uuid("bruce.wayne@example.com")

    # IAM service is synchronous
    with app.transaction_context() as ctx:
        iam_service = ctx[IamService]
        
        users_to_create = [
            (miles_id, "miles.morales@example.com", "password123", "miles_token"),
            (ororo_id, "ororo.munroe@example.com", "password123", "ororo_token"),
            (matt_id, "matt.murdock@example.com", "password123", "matt_token"),
            (bruce_id, "bruce.wayne@example.com", "password123", "bruce_token"),
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
            "id": generate_uuid("Xbox Series X"),
            "title": "Xbox Series X",
            "desc": "Lightly used Xbox Series X with 1 controller.",
            "price": 400,
            "seller_id": miles_id,
            "publish": True,
        },
        {
            "id": generate_uuid("PlayStation 5"),
            "title": "PlayStation 5 Disc Edition",
            "desc": "Brand new in box.",
            "price": 450,
            "seller_id": matt_id,
            "publish": True,
        },
        {
            "id": generate_uuid("Steam Deck OLED"),
            "title": "Steam Deck OLED 512GB",
            "desc": "Perfect condition, comes with carrying case.",
            "price": 500,
            "seller_id": bruce_id,
            "publish": True,
        },
        {
            "id": generate_uuid("Nintendo Switch"),
            "title": "Nintendo Switch OLED",
            "desc": "Includes dock and Joy-Cons.",
            "price": 300,
            "seller_id": ororo_id,
            "publish": True,
        },
        {
            "id": generate_uuid("NVIDIA RTX 4090"),
            "title": "NVIDIA GeForce RTX 4090 Founders Edition",
            "desc": "Used for light gaming, never mined on.",
            "price": 1500,
            "seller_id": bruce_id,
            "publish": True,
        },
        {
            "id": generate_uuid("ASUS ROG Ally"),
            "title": "ASUS ROG Ally Z1 Extreme",
            "desc": "Great handheld, basically a portable PC.",
            "price": 600,
            "seller_id": matt_id,
            "publish": True,
        },
        {
            "id": generate_uuid("Analogue Pocket"),
            "title": "Analogue Pocket - Black",
            "desc": "Plays original Game Boy cartridges perfectly.",
            "price": 220,
            "seller_id": ororo_id,
            "publish": True,
        },
        {
            "id": generate_uuid("PlayStation Portal"),
            "title": "PlayStation Portal Remote Player",
            "desc": "Stream your PS5 anywhere in the house.",
            "price": 200,
            "seller_id": miles_id,
            "publish": True,
        },
        {
            "id": generate_uuid("AMD Radeon RX 7900 XTX"),
            "title": "AMD Radeon RX 7900 XTX 24GB",
            "desc": "Flagship AMD GPU, dominates 4K gaming.",
            "price": 950,
            "seller_id": matt_id,
            "publish": True,
        },
        {
            "id": generate_uuid("Meta Quest 3"),
            "title": "Meta Quest 3 128GB",
            "desc": "Amazing mixed reality headset.",
            "price": 500,
            "seller_id": bruce_id,
            "publish": True,
        },
        {
            "id": generate_uuid("Unpublished Game Console"),
            "title": "Super Nintendo Classic (DRAFT)",
            "desc": "I haven't published this yet.",
            "price": 150,
            "seller_id": miles_id,
            "publish": False,
        },
        {
            "id": generate_uuid("Expired Laptop"),
            "title": "MacBook Pro M1 (EXPIRED)",
            "desc": "This listing has already ended.",
            "price": 1200,
            "seller_id": ororo_id,
            "publish": True,
            "expire_manually": True
        },
        {
            "id": generate_uuid("Vintage Camera"),
            "title": "Leica M6 (EXPIRED NO BIDS)",
            "desc": "This camera auction ended with zero bids.",
            "price": 2500,
            "seller_id": bruce_id,
            "publish": True,
            "expire_manually": True
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
        # Xbox (2 bids)
        {"listing_id": generate_uuid("Xbox Series X"), "bidder_id": ororo_id, "amount": 420},
        {"listing_id": generate_uuid("Xbox Series X"), "bidder_id": bruce_id, "amount": 450},
        
        # PS5 (1 bid)
        {"listing_id": generate_uuid("PlayStation 5"), "bidder_id": miles_id, "amount": 500},
        
        # Steam Deck (3 bids)
        {"listing_id": generate_uuid("Steam Deck OLED"), "bidder_id": ororo_id, "amount": 550},
        {"listing_id": generate_uuid("Steam Deck OLED"), "bidder_id": miles_id, "amount": 600},
        {"listing_id": generate_uuid("Steam Deck OLED"), "bidder_id": matt_id, "amount": 650},
        
        # Nintendo Switch (0 bids)
        
        # RTX 4090 (3 bids)
        {"listing_id": generate_uuid("NVIDIA RTX 4090"), "bidder_id": matt_id, "amount": 1600},
        {"listing_id": generate_uuid("NVIDIA RTX 4090"), "bidder_id": ororo_id, "amount": 1700},
        {"listing_id": generate_uuid("NVIDIA RTX 4090"), "bidder_id": miles_id, "amount": 1800},
        
        # ASUS ROG Ally (1 bid)
        {"listing_id": generate_uuid("ASUS ROG Ally"), "bidder_id": bruce_id, "amount": 650},
        
        # Analogue Pocket (2 bids)
        {"listing_id": generate_uuid("Analogue Pocket"), "bidder_id": miles_id, "amount": 230},
        {"listing_id": generate_uuid("Analogue Pocket"), "bidder_id": bruce_id, "amount": 250},
        
        # PlayStation Portal (0 bids)
        
        # RX 7900 XTX (1 bid)
        {"listing_id": generate_uuid("AMD Radeon RX 7900 XTX"), "bidder_id": ororo_id, "amount": 1000},
        
        # Meta Quest 3 (2 bids)
        {"listing_id": generate_uuid("Meta Quest 3"), "bidder_id": matt_id, "amount": 520},
        {"listing_id": generate_uuid("Meta Quest 3"), "bidder_id": miles_id, "amount": 550},
        
        # Expired Laptop (2 bids)
        {"listing_id": generate_uuid("Expired Laptop"), "bidder_id": matt_id, "amount": 1250},
        {"listing_id": generate_uuid("Expired Laptop"), "bidder_id": miles_id, "amount": 1300},
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

    # Manually expire specific listings
    logger.info("Manually expiring designated listings...")
    with app.transaction_context() as ctx:
        session = ctx["db_session"]
        expired_ids = [str(item["id"]) for item in listings if item.get("expire_manually")]
        if expired_ids:
            past_date = datetime.utcnow() - timedelta(days=2)
            for l_id in expired_ids:
                session.execute(
                    text("UPDATE bidding_listing SET data = jsonb_set(data, '{ends_at}', CAST(:past_date AS jsonb)) WHERE id = :id"),
                    {"past_date": f'"{past_date.isoformat()}"', "id": l_id}
                )
            logger.info(f"Expired {len(expired_ids)} listings in the bidding schema.")

if __name__ == "__main__":
    asyncio.run(seed_database())
