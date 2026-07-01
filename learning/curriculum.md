# Python DDD Learning Curriculum

## Context & Learning Objectives

The primary goal of this curriculum is to master **Domain-Driven Design (DDD)**, **Test-Driven Development (TDD)**, and **Clean Architecture** by systematically studying and interacting with the `python-ddd` reference codebase.

**Why this approach?**
The ultimate objective is to gain a deep, practical understanding of these architectural patterns—specifically repositories, ports, adapters, and use cases. This knowledge will be directly applied to refactor an existing work codebase into a highly maintainable, enterprise-grade template. This template is designed to empower a solo developer, ensuring that the codebase remains robust, cleanly separated, and easy to extend as the project grows.

This curriculum outlines the structure of our learning guide, breaking down these complex topics into digestible, hands-on chapters.

## Reference Materials

Throughout this curriculum, we will frequently refer to the following cornerstone books on Python architecture and TDD:
1. **[Cosmic Python (Architecture Patterns with Python)](https://www.cosmicpython.com/)** by Harry Percival and Bob Gregory: The primary guide for DDD, Clean Architecture, and enterprise patterns in Python.
2. **[Obey the Testing Goat (Test-Driven Development with Python)](https://www.obeythetestinggoat.com/)** by Harry Percival: The definitive guide for TDD and testing methodologies in Python.

## Chapter Structure

### Chapter 1: The Big Picture & Core Domain Modeling
*   **Concept:** Clean Architecture concentric circles, the Dependency Rule, Entities, and Value Objects.
*   **Codebase Focus:** `src/seedwork/domain/` (base classes) and `src/modules/bidding/domain/` (concrete implementations like `Listing` and `Bid`).
*   **Book Ref:** Cosmic Python Chapter 1 (Domain Modeling).

### Chapter 2: Enforcing Business Rules & Domain Events
*   **Concept:** How to keep invalid states out of your application and how parts of the system communicate asynchronously.
*   **Codebase Focus:** `seedwork/domain/rules.py`, `modules/bidding/domain/rules.py` (e.g., `BidCanBeRetracted`), and `events.py`.
*   **Book Ref:** Cosmic Python Chapter 7 & 8 (Events and the Message Bus).

### Chapter 3: The Application Layer (Commands, Queries, and Use Cases)
*   **Concept:** CQRS (Command Query Responsibility Segregation) and how the application layer orchestrates the domain.
*   **Codebase Focus:** `modules/bidding/application/command/place_bid.py` and `modules/bidding/application/query/get_bidding_details.py`.
*   **Book Ref:** Cosmic Python Chapter 4 & 11 (Service Layer & CQRS).

### Chapter 4: The Infrastructure Layer (Repositories & Data Mappers)
*   **Concept:** Ports and Adapters, decoupling the database from the business logic.
*   **Codebase Focus:** `seedwork/infrastructure/repository.py`, `ListingRepository`, and SQLAlchemy data mapping.
*   **Book Ref:** Cosmic Python Chapter 2 (Repository Pattern).

### Chapter 5: TDD in Action (Testing the Domain)
*   **Concept:** Writing pure, fast unit tests without frameworks or databases.
*   **Codebase Focus:** `modules/bidding/tests/domain/test_bidding.py`.
*   **Book Ref:** Obey the Testing Goat & Cosmic Python Chapter 3 (Coupling and Abstractions).

### Chapter 6: Delivery Mechanisms & Dependency Injection
*   **Concept:** How the outside world (Web APIs, UIs) talks to your application and how dependencies are wired together.
*   **Codebase Focus:** `src/api/routers/bidding.py` (FastAPI) and `src/config/container.py` (Dependency Injector).
*   **Book Ref:** Cosmic Python Chapter 13 (Dependency Injection).

### Chapter 7: The Foundation (Message & Command Bus)
*   **Concept:** Understanding the inner workings of the internal message bus, event dispatching, and transaction context management (formerly `lato`).
*   **Codebase Focus:** `src/seedwork/foundation/` (specifically `application.py`, `transaction_context.py`, and `dependency_provider.py`).
*   **Book Ref:** Cosmic Python Chapter 8 (Events and the Message Bus) & Chapter 9 (The Message Bus).
