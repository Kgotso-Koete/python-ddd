# Chapter 9: Reusable UI Authentication via FastAPI Dependencies

## Concept: DRY Security at the Route Level

In a secure Web Application, almost every action (creating a resource, viewing private details, performing an action) requires verifying the user's identity. If you manually check the user's session token inside the body of every HTTP route, you create two major problems:

1. **WET (Write Everything Twice) Code:** You end up copying and pasting the same 5 lines of authentication logic across dozens of routes.
2. **Security Vulnerabilities:** If a new developer creates a new route and simply forgets to copy-paste the auth block, that route is instantly vulnerable to unauthorized access.

### The FastAPI Solution: `Depends()`

FastAPI solves this brilliantly using **Dependencies**. A dependency is simply a function that runs *before* your main route function. If the dependency fails (e.g., the user is not logged in), it can raise an Exception to halt the request before it even reaches your business logic.

## Codebase Focus

### 1. Defining the Dependencies (`src/web/dependencies.py`)

We created two distinct dependencies for the UI:

*   **`get_current_ui_user_optional`**: Used for public pages (like the Catalog Homepage). It reads the `access_token` cookie and returns a `User` if one exists, or `None` if it doesn't. It never blocks the request.
*   **`get_current_ui_user`**: Used for protected pages (like creating a listing). It depends on the optional function, but if the user is `None`, it raises a `NotAuthenticatedException`.

### 2. Global Exception Handling (`src/api/main.py`)

When `NotAuthenticatedException` is raised, we don't want the user to see a raw JSON error. We want to cleanly redirect them to the login page. We added a global exception handler in `main.py` that catches this exception and returns a `RedirectResponse(url="/ui/login", status_code=303)`.

### 3. Securing the Routes (`src/web/router.py`)

By injecting the dependency into the route signature, the route is automatically secured:

```python
# Before (Vulnerable to copy-paste errors)
@router.post("/ui/catalog/new")
async def new_listing_submit(request: Request, ctx: TransactionContext = Depends(get_transaction_context)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=303)
    current_user = ctx[IamService].find_user_by_access_token(access_token)
    if not current_user:
        return RedirectResponse(url="/ui/login", status_code=303)
    
    # ... business logic ...

# After (Secure by Default)
@router.post("/ui/catalog/new")
async def new_listing_submit(
    request: Request,
    ctx: TransactionContext = Depends(get_transaction_context),
    current_user: User = Depends(get_current_ui_user)  # <--- Auth enforced here!
):
    # ... business logic ...
```

## How this translates to Truck Delivery

In your B2B on-demand truck delivery app, you will have multiple types of users (e.g., Drivers, B2B Dispatchers, Internal Admins). 

You can create specific dependencies to enforce granular Role-Based Access Control (RBAC):

```python
# Check if they are a driver
async def get_current_driver(user: User = Depends(get_current_api_user)) -> Driver:
    if not user.is_driver:
        raise HTTPException(status_code=403, detail="Only drivers can accept trips")
    return user

# Check if they belong to a specific B2B company
async def get_b2b_client(user: User = Depends(get_current_api_user)) -> B2BClient:
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Must belong to a corporate account")
    return user
```

By placing `Depends(get_current_driver)` on a route like `POST /trips/{id}/accept`, you guarantee that no standard user or B2B client can accidentally accept a trip, and your route body remains 100% focused on business logic.
