# Future Architecture Improvements

While `python-ddd` serves as an excellent foundation with modern tooling (FastAPI, Pydantic, Alembic) and explicit domain building blocks (`seedwork/`), as the application scales—specifically into domains like truck-hiring with complex workflows and WhatsApp integration—we need to incorporate advanced patterns from textbook Clean Architecture.

This document unifies the key architectural lessons and ideas to implement in the future to ensure the codebase remains maintainable, decoupled, and scalable.

## Progress Checklist
- [x] **1. Output Boundaries and The Presenter Pattern**
- [ ] **2. Process Managers (Sagas) for Cross-Module Orchestration**
- [ ] **3. Background Task Queues (Redis/RQ/Celery)**
- [x] **4. Ditching the "Magic" Frameworks — Remove `lato` Dependency** (Internalized as `seedwork.foundation`)
- [ ] **5. Integration with External Infrastructure**
- [ ] **6. Proper Application Layer Testing**
- [ ] **7. Strict Package Boundaries**
- [ ] **8. Explicit Facades / Application Interfaces**
- [x] **9. Missing Business Rules:** Added `SellerCannotBidOnOwnListing` to `modules/bidding`.
- [ ] **10. Reusable UI Authentication via FastAPI Dependencies**
- [ ] **11. REST API JWT Authentication**
- [ ] **12. Pagination for API and Web UI**

---

## 1. Output Boundaries and The Presenter Pattern
Currently, `python-ddd` tightly couples the Application layer to the API response format. A Command or Query is executed, and raw JSON is returned.

**The Improvement:** Implement **Output Boundaries** and **Presenters**. 
- Instead of returning raw data, the Application layer passes data to an interface (e.g., `BookingOutputBoundary`).
- You create specific implementations for each delivery mechanism (e.g., `WhatsAppBookingPresenter`, `WebBookingPresenter`, `ApiBookingPresenter`).
- **Why it's crucial:** This allows the exact same core business logic to format a JSON response, render an HTML template, or send a WhatsApp message without polluting your use cases or routers with messy `if/else` logic.

## 2. Process Managers (Sagas) for Cross-Module Orchestration
Currently, modules (`bidding`, `catalog`) are distinct but lack examples of complex, asynchronous workflows spanning multiple modules.

**The Improvement:** Introduce **Process Managers** (or Sagas).
- A Process Manager acts as a centralized coordinator. It listens to Domain Events from one module and issues Commands to other modules.
- **Why it's crucial:** Truck hiring is deeply workflow-based. You don't want the `Orders` domain to be tightly coupled to `Dispatch`. Instead, a `BookingProcessManager` listens for a `BookingPaid` event, notifies the trucking company, waits for acceptance, and then issues a `DispatchTruckCommand`.
- **Proof of Concept:** The `clean-architecture` repo implements this perfectly in `auctioning_platform/processes/paying_for_won_item/`, serving as a fantastic template for how to decouple cross-module workflows.

## 3. Background Task Queues (Redis/RQ/Celery)
Currently, events are fired synchronously within the transaction context.

**The Improvement:** Implement the **Outbox Pattern** and utilize a message broker and worker queue to process asynchronous infrastructure tasks outside the main HTTP request lifecycle.
- **Why it's crucial:** When a user books a truck via WhatsApp, you need to send an email receipt, ping a GPS API to find the nearest truck, and notify the driver. Doing this synchronously blocks the server response, causing a delayed reply to the user. Fast webhooks require delegating slow tasks to background workers.
- **Proof of Concept:** The `clean-architecture` repo uses an `outbox.py` implementation alongside background queues (Redis/RQ) to process these side-effects reliably, completely protecting the API's response times.

## 4. Ditching the "Magic" Frameworks — Remove `lato` Dependency
The current version of `python-ddd` abstracts away core architectural concepts (Unit of Work, Event Dispatching) behind the 3rd-party `lato` library. **Critically, `lato` is maintained by a single developer**, making it a supply chain risk sitting in the most foundational layer of the codebase (`seedwork`). The `Command` base class, `ApplicationModule` handler registry, and dependency resolution all flow through `lato` — meaning an abandoned or breaking update could compromise the entire application architecture.

**The Improvement:** Architecture should not be a pip dependency; it should be explicitly modeled in the codebase. Replace `lato` with custom implementations of:
- `Command` / `Query` base classes (thin Pydantic `BaseModel` wrappers — ~10 lines each)
- `ApplicationModule` handler registry (a dictionary mapping message types to handler functions — ~50 lines)
- Dependency resolution via type-hint inspection (already partially implemented in `seedwork/application/__init__.py`'s `DependencyProvider`)
- **Why it's crucial:** Building the `EventBus`, `TransactionContext`, and Use Case handlers from scratch ensures developers understand exactly where transactions begin and end, and eliminates a single-maintainer dependency from the most critical layer. *(Note: The older custom `seedwork` did this beautifully before `lato` was introduced.)*

## 5. Integration with External Infrastructure
**The Improvement:** Cleanly abstract third-party services (like Stripe for payments or Twilio/Meta for WhatsApp) behind interfaces, keeping the core domain pure.
- **Why it's crucial:** The application will inevitably require integrations with external gateways.
- Define an interface in the application layer (e.g., `IPaymentGateway` or `INotificationService`). Implement the actual HTTP requests to the third-party service entirely within the `infrastructure` layer. The business logic remains unaware of whether an SMS or a WhatsApp was sent.

## 6. Proper Application Layer Testing
Currently, application-layer tests frequently spin up a real test database (Postgres or SQLite).

**The Improvement:** Test Application Use Cases using **In-Memory Repositories** and **Mocked Output Boundaries**.
- **Why it's crucial:** This proves the entire application flow (Command → Handler → Domain → Repo → EventBus → Presenter) works flawlessly in milliseconds, without the massive overhead of database I/O. It separates slow integration tests from fast architectural tests.
- **How to do it:** The Foundation already ships with `override_ctx` in `src/seedwork/foundation/testing.py`. Use it to temporarily swap a real database-backed `ListingRepository` for a fast in-memory fake during tests. This utility exists in the codebase but is **currently unused** — see [Chapter 7](./chapter_7.md) for details.
- **Bonus:** The deprecated tests in `src/seedwork/tests/application/` (currently skipped via `@pytest.mark.skip`) should also be rewritten to verify the new `foundation` components directly.

## 7. Strict Package Boundaries
Currently, all modules live inside a single `src/modules/` directory, relying on developer discipline to prevent cross-imports (e.g., the `bidding` code accidentally importing a database model from `catalog`).

**The Improvement:** Break modules into physically separate, installable Python packages with their own `setup.py` or `pyproject.toml` files.
- **Why it's crucial:** This enforces strict architectural boundaries at the package manager level—modules physically cannot cross-import unless explicitly declared as a dependency, forcing developers to communicate via explicit Domain Events or API contracts.
- **Proof of Concept:** The `clean-architecture` repo enforces this strictly. Notice how its `auctions`, `payments`, and `shipping` modules each have their own `setup.py`, making it physically impossible for them to bypass the architecture.

## 8. Explicit Facades / Application Interfaces
Currently, inter-module communication is somewhat informal or relies solely on events.

**The Improvement:** Expose strict interfaces or "Facades" for modules that must communicate synchronously.
- **Why it's crucial:** When one module absolutely must query another module for data, having an explicit Facade hides all internal complexities and database models of the queried module, providing a strict contract.
- **Proof of Concept:** The `clean-architecture` repo uses strict facades (e.g., `PaymentsFacade`) to ensure modules don't directly access each other's internals.

## 9. Missing Business Rules
- **The Improvement:** Add a `SellerCannotBidOnOwnListing` Business Rule to `src/modules/bidding/domain/rules.py` and enforce it in `Listing.place_bid()`.
- **Why it's crucial:** The domain currently allows a seller to bid on their own listing (shill bidding). Catching and fixing these missing real-world constraints is a great exercise for practicing Domain-Driven Design in the `domain` layer.

## 10. Reusable UI Authentication via FastAPI Dependencies
Currently, the `src/web/router.py` duplicates the same block of code across multiple protected routes to verify the `access_token` cookie, redirect on failure, and fetch the current user. If a developer forgets to copy-paste this block on a new route, it creates a severe security vulnerability.

**The Improvement:** Abstract this logic into a reusable FastAPI `Depends()` function (e.g., `get_current_ui_user(request: Request) -> User`). This ensures DRY code and enforces UI security cleanly at the route signature level without manual copy-pasting.

## 11. REST API JWT Authentication
Currently, the REST API endpoints (like `/bidding/{listing_id}/place_bid`) blindly trust the `bidder_id` provided in the JSON payload without verifying the user's identity. 

**The Improvement:** Implement standard JWT Bearer token authentication for the API routes using FastAPI's `HTTPBearer` security schemes. The API should extract the user ID directly from the validated token rather than trusting the request body.

## 12. Pagination for API and Web UI
Currently, `GetAllListings` returns every listing in the database in a single response. As the catalog grows, this will cause performance issues: slow page loads, excessive memory usage, and a poor user experience when scrolling through hundreds of items.

**The Improvement:**
- **Backend:** Update `GetAllListings` to accept `limit` and `offset` (or `page` and `page_size`) parameters. The SQL query should use `.limit()` and `.offset()` to only fetch the requested page of results. The Output DTO should include pagination metadata (total count, current page, total pages).
- **API Layer:** Return pagination metadata alongside the data array (e.g., `{ data: [...], total: 150, page: 1, page_size: 20 }`).
- **Web UI:** Add "Previous" / "Next" navigation buttons (or page numbers) to the catalog listing page.
- **Why it's crucial:** Pagination is a fundamental requirement for any production system dealing with growing datasets. Without it, response times degrade linearly with data volume.
