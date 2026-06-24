# Chapter 2: Enforcing Business Rules & Domain Events

Welcome to Chapter 2! Now that we understand Entities and Value Objects (the *nouns* of our system), we need to talk about the *verbs* and the *rules*.

In Clean Architecture, the **Domain Layer** must protect its own invariants. It should be literally impossible to put the Domain into an invalid state.

---

## Part 1: Enforcing Business Rules

In a standard application, you might put validation logic in your controllers or API routes (e.g., checking if a bid is high enough inside the FastAPI route before saving to the database). 

**In DDD, this is a massive anti-pattern.** Business rules belong entirely in the Domain Layer. If a rule changes, you should only have to update the Domain, not the API.

### 📚 Book Reference
> **Cosmic Python, Chapter 7 & 8**: *"Events and the Message Bus"* discusses how systems communicate, but the foundation is that the Domain model raises errors or events when rules are evaluated.

### How `python-ddd` Does It
Take a look at [src/seedwork/domain/rules.py](../src/seedwork/domain/rules.py). 
It defines a base `BusinessRule` class. A rule is simply a class that returns `True` or `False` from an `is_broken()` method.

Now look at [src/modules/bidding/domain/rules.py](../src/modules/bidding/domain/rules.py).
Let's analyze `PriceOfPlacedBidMustBeGreaterOrEqualThanNextMinimumPrice`:

```python
class PriceOfPlacedBidMustBeGreaterOrEqualThanNextMinimumPrice(BusinessRule):
    __message = "Placed bid must be greater or equal than {next_minimum_price}"

    current_price: Money
    next_minimum_price: Money

    def is_broken(self) -> bool:
        return self.current_price < self.next_minimum_price
```
Notice how clean this is? It's pure Python. It uses the `Money` Value Object. It doesn't know about HTTP requests or databases.

Where is this rule enforced? Open [src/modules/bidding/domain/entities.py](../src/modules/bidding/domain/entities.py) and look at the `place_bid` method inside the `Listing` aggregate root:

```python
    def place_bid(self, bid: Bid):
        # ... (some logic)
        self.check_rule(
            rules.PriceOfPlacedBidMustBeGreaterOrEqualThanNextMinimumPrice(
                current_price=bid.max_price,
                next_minimum_price=self.get_next_minimum_bid_price(),
            )
        )
        self.bids.append(bid)
```

**Why this is amazing:**
1. **Self-Documenting Code:** The rule name exactly describes the business requirement. You don't need comments to explain what the `if` statement is doing.
2. **Testability:** You can test this rule in 1 millisecond without a database.
3. **Impenetrable Domain:** You literally cannot call `listing.place_bid()` with a low price without an exception being thrown. The Domain defends itself.

---

## Part 2: Domain Events (The "Publish-Subscribe" inside your App)

When a domain object changes state, other things in the system usually need to know about it.
* If a bid is placed, we might need to email the previous highest bidder.
* If a listing is published in the Catalog, we need to create a counterpart in the Bidding module (as we saw with our database wiping issue earlier!).

**Anti-pattern:** The `place_bid` method directly calls `email_service.send()`. This tightly couples your pure domain to an external email API!

**DDD Pattern:** The Domain simply shouts: *"Hey, a BidWasPlaced!"* and doesn't care who is listening.

### Look at the Code
Open [src/modules/bidding/domain/events.py](../src/modules/bidding/domain/events.py):

```python
class BidWasPlaced(DomainEvent):
    listing_id: GenericUUID
    bidder_id: GenericUUID

class HighestBidderWasOutbid(DomainEvent):
    listing_id: GenericUUID
    outbid_bidder_id: GenericUUID
```

Back in the `Listing` entity's `place_bid` method, after the bid is added to the list, you will see something like this:
```python
        self.record_event(
            events.HighestBidderWasOutbid(
                listing_id=self.id, outbid_bidder_id=highest_bid.bidder.id
            )
        )
```

**What is `record_event`?**
Because `Listing` inherits from `AggregateRoot` (in `seedwork/domain/entities.py`), it has an internal list called `_events`. When the listing does something important, it adds an event to this list. 

Later, the Application Layer (specifically the Unit of Work middleware we'll look at in Chapter 3) will automatically collect all these recorded events and trigger the appropriate handlers (like sending an email or updating another module).

---

## Part 3: Test-Driven Development (TDD) for Business Rules

Because our Business Rules are pure Python classes (like `PriceOfPlacedBidMustBeGreaterOrEqualThanNextMinimumPrice`), TDD is a breeze.

If your product manager says: *"A user cannot place a bid lower than the starting price"*, you do not need to write an API route to test this. You simply:
1. Write a test in `test_bidding.py` that creates a `Listing` and a `Bid`.
2. Call `listing.place_bid(bid)`.
3. Assert that it raises a `BusinessRuleValidationException`.

Because the rules are decoupled from infrastructure, you can test hundreds of rules in under a second!

### Running the Tests

To run the entire suite of Domain Layer tests (which covers everything in Chapters 1 & 2), run this from your terminal:
```bash
poe test_domain
```

To run a "micro-test" specifically targeting a **Business Rule** (e.g., verifying you cannot bid on an ended listing), run this:
```bash
pytest src/modules/bidding/tests/domain/test_bidding.py::test_cannot_place_bid_if_listing_ended
```

---

## 🧪 Hands-On Exercise #2

Let's test your understanding of Business Rules and Events:

1. **Find the Retraction Rule:** Open [src/modules/bidding/domain/rules.py](../src/modules/bidding/domain/rules.py) and read the `BidCanBeRetracted` rule. What are the two time-based conditions required for a user to successfully retract a bid?
2. **Find the Event Trigger:** Open [src/modules/catalog/domain/entities.py](../src/modules/catalog/domain/entities.py). Look at the `publish()` method of the `Listing` draft. What exact `DomainEvent` is recorded when a draft is successfully published?

> [!NOTE]
> Take a moment to read through `rules.py` and `events.py` in both the `bidding` and `catalog` modules to see how simple and isolated they are.
> 
> Let me know when you are ready for **Chapter 3**, where we learn how the Application Layer (Commands, Queries, and CQRS) orchestrates all of this!
