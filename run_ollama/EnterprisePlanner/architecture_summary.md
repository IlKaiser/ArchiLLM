# Architecture Summary

## Microservices

| Name | Description | User Stories |
|---|---|---|
| API Gateway | Single entry point for all clients, routing and orchestration | - Serve as entry point<br>- Route requests to appropriate services |
| Authentication Service | Handles user authentication and authorization | - Verify credentials<br>- Issue tokens |
| Catalog Service | Provides product catalog information | - Retrieve product details |
| Pricing Service | Returns pricing information for products | - Calculate price based on quantity |
| Inventory Service | Manages product inventory levels | - Check stock availability |
| Order Service | Processes orders and manages order lifecycle | - Create, update, cancel orders |
| Notification Service | Sends notifications to users | - Email, push notifications |
| Reporting Service | Generates business reports and analytics | - Produce sales reports |

## Architectural Patterns

| Group | Pattern(s) | Involved Services | Rationale |
|---|---|---|---|
| Design Patterns | Database per Service, Saga, API Composition, CQRS, Domain event, Event sourcing | Multiple services | Provide solutions for data isolation, distributed transactions, query composition, separation of concerns, and eventual consistency |

## Datastores

| Name | Type | Owning Service | Description |
|---|---|---|---|
| PostgreSQL | Relational Database | API Gateway | Single entry point for clients |
| MongoDB | Document Store | Authentication Service | Manages user authentication |
| ElasticSearch | Search Engine | Catalog Service | Product catalog search |
| DynamoDB | Key-Value/NoSQL Database | Pricing Service | Stores product pricing |
| PostgreSQL | Relational Database | Inventory Service | Tracks inventory levels |
| MySQL | Relational Database | Order Service | Handles order processing |
| Redis | In-Memory Data Store | Notification Service | Stores notifications |
| ClickHouse | Columnar Data Warehouse | Reporting Service | Analytical queries and reporting |

## Inter-Service Dependencies

| From | To | Protocol | Description |
|---|---|---|---|
| API Gateway | auth-service | REST | Client requests authentication service |
| auth-service | catalog-service | REST | Authentication service queries catalog service |
| catalog-service | pricing-service | REST | Catalog service queries pricing service |
| inventory-service | order-service | REST | Inventory service provides stock info for order service |
| notification-service | order-service | WebSocket | Order service receives real-time notifications |
| reporting-service | analytics-service | REST | Reporting service exposes analytics data |

**Legend**

- **REST**: Synchronous HTTP request/response interactions.
- **WebSocket**: Persistent bidirectional communication channel.
- **Event**: Asynchronous message published to a broker; consumed by interested services.
- **gRPC**: High-performance remote procedure call protocol (not used in current diagram).