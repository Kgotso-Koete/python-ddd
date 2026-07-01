from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Annotated

from seedwork.foundation import Application, TransactionContext
from api.dependencies import get_application, get_transaction_context
from modules.catalog.application.query.get_all_listings import GetAllListings

router = APIRouter(tags=["web"])

templates = Jinja2Templates(directory="src/web/templates")

@router.get("/ui", response_class=HTMLResponse)
async def home(
    request: Request,
    app: Annotated[Application, Depends(get_application)],
    ctx: TransactionContext = Depends(get_transaction_context)
):
    query = GetAllListings()
    result = await app.execute_async(query)
    
    from modules.iam.application.services import IamService
    from seedwork.domain.value_objects import GenericUUID
    iam_service = ctx[IamService]
    
    for listing in result:
        try:
            seller = iam_service.user_repository.get_by_id(GenericUUID(listing["seller_id"]))
            listing["seller_email"] = seller.email if seller else "Unknown Seller"
        except Exception:
            listing["seller_email"] = "Unknown Seller"
    
    current_user = None
    access_token = request.cookies.get("access_token")
    if access_token:
        current_user = iam_service.find_user_by_access_token(access_token)
    
    return templates.TemplateResponse(
        "catalog.html", 
        {"request": request, "listings": result, "current_user": current_user}
    )

@router.get("/ui/catalog/new", response_class=HTMLResponse)
async def new_listing_page(
    request: Request,
    ctx: TransactionContext = Depends(get_transaction_context)
):
    from fastapi import status
    from fastapi.responses import RedirectResponse
    from modules.iam.application.services import IamService
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)
        
    current_user = ctx[IamService].find_user_by_access_token(access_token)
    if not current_user:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse("create_listing.html", {"request": request, "current_user": current_user})


@router.post("/ui/catalog/new")
async def new_listing_submit(
    request: Request,
    app: Annotated[Application, Depends(get_application)],
    title: str = Form(...),
    description: str = Form(...),
    ask_price: int = Form(...),
    ctx: TransactionContext = Depends(get_transaction_context)
):
    import uuid
    from fastapi import status
    from fastapi.responses import RedirectResponse
    from modules.iam.application.services import IamService
    from modules.catalog.application.command.create_listing_draft import CreateListingDraftCommand
    from modules.catalog.application.command.publish_listing_draft import PublishListingDraftCommand
    from seedwork.domain.value_objects import GenericUUID, Money
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)
        
    current_user = ctx[IamService].find_user_by_access_token(access_token)
    if not current_user:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)

    listing_id = GenericUUID(str(uuid.uuid4()))
    seller_id = GenericUUID(str(current_user.id))
    
    try:
        # Create draft
        await app.execute_async(
            CreateListingDraftCommand(
                listing_id=listing_id,
                title=title,
                description=description,
                ask_price=Money(ask_price, "USD"),
                seller_id=seller_id
            )
        )
        
        # Immediately publish
        await app.execute_async(
            PublishListingDraftCommand(
                listing_id=listing_id,
                seller_id=seller_id
            )
        )
        

        
        return RedirectResponse(url=f"/ui/catalog/{str(listing_id)}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            "create_listing.html", 
            {"request": request, "current_user": current_user, "error": str(e)}
        )


@router.get("/ui/catalog/{listing_id}", response_class=HTMLResponse)
async def listing_details(
    listing_id: str,
    request: Request,
    app: Annotated[Application, Depends(get_application)],
    success: str = None,
    ctx: TransactionContext = Depends(get_transaction_context)
):
    from modules.catalog.application.query.get_listing_details import GetListingDetails
    from modules.bidding.application.query.get_bidding_details import GetBiddingDetails
    from seedwork.domain.value_objects import GenericUUID
    
    listing_uuid = GenericUUID(listing_id)
    
    # 1. Fetch catalog details
    listing_query = GetListingDetails(listing_id=listing_uuid)
    # The application layer returns a dictionary for listing_query
    listing_result = await app.execute_async(listing_query)
    
    # 2. Fetch auction/bidding details
    auction_result = None
    try:
        auction_query = GetBiddingDetails(listing_id=listing_uuid)
        auction_result = await app.execute_async(auction_query)
    except Exception:
        # Bidding might not exist if not published or errors
        pass
        
    from modules.iam.application.services import IamService
    iam_service = ctx[IamService]
    
    try:
        seller = iam_service.user_repository.get_by_id(GenericUUID(listing_result["seller_id"]))
        listing_result["seller_email"] = seller.email if seller else "Unknown Seller"
    except Exception:
        listing_result["seller_email"] = "Unknown Seller"

    current_user = None
    access_token = request.cookies.get("access_token")
    if access_token:
        current_user = iam_service.find_user_by_access_token(access_token)
        
    return templates.TemplateResponse(
        "listing_details.html",
        {
            "request": request, 
            "listing": listing_result, 
            "auction": auction_result,
            "current_user": current_user,
            "success": success
        }
    )

@router.post("/ui/catalog/{listing_id}/bid")
async def place_bid(
    listing_id: str,
    request: Request,
    app: Annotated[Application, Depends(get_application)],
    amount: int = Form(...),
    ctx: TransactionContext = Depends(get_transaction_context)
):
    from fastapi import status
    from fastapi.responses import RedirectResponse
    from modules.bidding.application.command.place_bid import PlaceBidCommand
    from seedwork.domain.value_objects import GenericUUID
    from modules.iam.application.services import IamService
    
    # 1. Authenticate user from cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)
        
    current_user = ctx[IamService].find_user_by_access_token(access_token)
    if not current_user:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)

    # 2. Execute command
    command = PlaceBidCommand(
        listing_id=GenericUUID(listing_id),
        bidder_id=GenericUUID(str(current_user.id)),
        amount=amount,
        currency="USD"
    )
    
    try:
        await app.execute_async(command)
        

        # If successful, redirect back to the listing to see the updated bid
        return RedirectResponse(url=f"/ui/catalog/{listing_id}?success=Bid+placed+successfully", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        # 3. If bidding fails (e.g. DomainException) we render the page with an error
        from modules.catalog.application.query.get_listing_details import GetListingDetails
        from modules.bidding.application.query.get_bidding_details import GetBiddingDetails
        listing_uuid = GenericUUID(listing_id)
        listing_result = await app.execute_async(GetListingDetails(listing_id=listing_uuid))
        
        auction_result = None
        try:
            auction_result = await app.execute_async(GetBiddingDetails(listing_id=listing_uuid))
        except Exception:
            pass
            
        return templates.TemplateResponse(
            "listing_details.html",
            {
                "request": request, 
                "listing": listing_result, 
                "auction": auction_result,
                "current_user": current_user,
                "error": str(e)
            }
        )


@router.get("/ui/logout")
async def logout(request: Request):
    from fastapi import status
    from fastapi.responses import RedirectResponse
    response = RedirectResponse(url="/ui", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/ui/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/ui/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    ctx: TransactionContext = Depends(get_transaction_context)
):
    from modules.iam.application.services import IamService
    from modules.iam.application.exceptions import InvalidCredentialsException
    
    iam_service = ctx[IamService]
    try:
        user = iam_service.authenticate_with_name_and_password(email, password)
        # Create redirect to catalog and set a cookie!
        from fastapi import status
        from fastapi.responses import RedirectResponse
        response = RedirectResponse(url="/ui", status_code=status.HTTP_303_SEE_OTHER)
        # Set access token cookie
        response.set_cookie(key="access_token", value=user.access_token, httponly=True)
        return response
    except InvalidCredentialsException:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"})

@router.get("/ui/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/ui/register")
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    ctx: TransactionContext = Depends(get_transaction_context)
):
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Passwords do not match"})
    
    from modules.iam.application.services import IamService
    import uuid
    from fastapi import status
    from fastapi.responses import RedirectResponse
    
    iam_service = ctx[IamService]
    try:
        user = iam_service.create_user(
            user_id=uuid.uuid4(),
            email=email,
            password=password,
            access_token=str(uuid.uuid4())
        )
        response = RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)
        return response
    except ValueError as e:
        return templates.TemplateResponse("register.html", {"request": request, "error": str(e)})
