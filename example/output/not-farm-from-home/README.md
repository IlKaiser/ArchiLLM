# Microservices Architecture Example

## Microservices Implemented

- **Authentication Service**: Handles user registration, login, logout, and session management for all user types. Uses the **aggregate pattern** for authentication/session consistency.
- **User Profile Service**: Manages user profile information for Clients and Agricultural Companies. Uses the **aggregate pattern** for profile consistency.
- **Agricultural Company Service**: Manages Agricultural Company data, including registration, location, and listing companies. Uses the **aggregate pattern** for company data consistency.
- **Product Catalog Service**: Handles product inventory for Agricultural Companies, including adding, removing, modifying, and listing products, as well as highlighting seasonal products. Uses the **aggregate pattern** for inventory, and **domain event pattern** for product changes. Supports **saga pattern** for order coordination.
- **Cart Service**: Manages the shopping cart for Clients, including adding, removing, and viewing products. Uses the **aggregate pattern** for cart logic and **domain event pattern** for cart changes.
- **Order Service**: Handles order creation and management, including selecting a pickup date for reserved products. Uses the **aggregate pattern** for order lifecycle, **saga pattern** for coordination, and **domain event pattern** for order events.
- **Admin Management Service**: Allows administrators to manage users, including deleting malicious users. Uses the **aggregate pattern** for admin actions and **domain event pattern** for admin events.

## Patterns Used

- **Aggregate Pattern**: Used in all services to encapsulate business logic and ensure consistency within each service boundary.
- **Domain Event Pattern**: Used in Product Catalog, Cart, Order, and Admin Management services to emit events on significant changes.
- **Saga Pattern**: Used in Order Service (with Product Catalog and Cart) to coordinate distributed transactions for order creation.
- **API Composition**: Used for queries that require data from multiple services (e.g., showing a company's products or a user's orders).

## Datastores

Each service uses its own datastore (not shown in code, but referenced in the architecture):
- AuthenticationDB, UserProfileDB, CompanyDB, ProductCatalogDB, CartDB, OrderDB, AdminDB

## Running the System

1. Build all services with Maven (`mvn clean package` in each service folder).
2. Run `docker-compose up --build` from the root directory.
3. Access the frontend at [http://localhost:8080](http://localhost:8080) to test login and other endpoints.

## Note

This is a simplified example for demonstration. In production, add real persistence, security, and inter-service communication.