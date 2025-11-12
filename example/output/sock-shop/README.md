# SockShop Microservices Architecture

## Microservices Implemented

- **Catalog Service**: Manages the sock product catalog, including browsing, listing, and inventory management. Uses the Aggregate pattern for product consistency, CQRS for read/write optimization, and Domain Events for inventory/product updates.
- **Cart Service**: Handles shopping cart operations such as adding, updating, and viewing items in the cart. Uses Aggregate for cart consistency and CQRS for efficient cart queries and updates.
- **Order Service**: Processes orders, manages order history, and supports order confirmation and status updates. Uses Aggregate for order lifecycle, Saga for process coordination with Payment Service, and Domain Events for order status changes.
- **Payment Service**: Handles secure payment processing during checkout. Uses Aggregate for transaction consistency and participates in Saga and Domain Event patterns for order/payment coordination.
- **Rating Service**: Allows customers to rate their purchase experience. Uses Aggregate for rating consistency and CQRS for separating rating submission from queries.
- **Logging Service**: Collects and stores logs for monitoring, debugging, and admin review. Uses Event Sourcing to capture log events and Domain Events to receive logs from other services.
- **Monitoring Service**: Monitors service health and performance, integrates with Prometheus, and provides real-time alerts. Uses Domain Events to consume events from other services for monitoring and alerting.

## Patterns Used

- **Aggregate**: Ensures data consistency within each microservice's main entity (e.g., Product, Cart, Order, Payment, Rating).
- **CQRS (Command Query Responsibility Segregation)**: Separates read and write operations for performance and scalability (Catalog, Cart, Rating).
- **Domain Event**: Publishes and consumes events for inter-service communication (Catalog, Order, Payment, Logging, Monitoring).
- **Saga**: Coordinates long-running transactions across Order and Payment services.
- **Event Sourcing**: Used in Logging Service to store a sequence of log events.

## Datastores

Each microservice has its own PostgreSQL database for data isolation and autonomy.

## Frontend

A simple React frontend is provided to test the Catalog Service. It can be extended to interact with other services.

## Deployment

Use `docker-compose up --build` to start all services and databases. Each service is accessible on its respective port (see `docker-compose.yml`).
