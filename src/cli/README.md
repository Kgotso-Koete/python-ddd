# CLI (Command Line Interface)

The `cli` module demonstrates how to interact with the Application Layer (Use Cases) directly via the command line, completely bypassing FastAPI and the Web UI.

This is made possible by the **Output Boundary / Presenter Pattern**. Because our Use Cases do not know about HTTP requests or JSON responses, they can be executed by any delivery mechanism. In this module, we use a custom CLI Presenter that formats the Use Case output for the terminal.

## How to run the CLI script

1. Ensure your database is running:
```bash
poe compose_up
```

2. (Optional) If this is your first time, apply migrations:
```bash
cd src
alembic upgrade head
```

3. Run the script using Poe the Poet from the project root:
```bash
poe cli
```

## Why use a CLI in a web application?

In a real-world commercial application, you often need to execute business logic outside the context of a user clicking a button on a website. Common use cases include:

1. **Cron Jobs & Scheduled Tasks**: Running a nightly script to expire old listings, generate daily financial reports, or send bulk marketing emails.
2. **Data Migrations & Seeding**: Running scripts to backfill missing data or seed a new environment with test data.
3. **Admin Operations**: Allowing developers or sysadmins to perform emergency actions (like suspending an abusive user) directly from a secure server terminal without needing to build an entire Admin UI for it first.
4. **Message Queue Consumers**: Background workers (like Celery or RabbitMQ consumers) are essentially headless scripts that execute commands based on incoming messages, similar to how a CLI works.
