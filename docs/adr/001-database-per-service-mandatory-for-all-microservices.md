# ADR-001: Database per service (MANDATORY for all microservices)

**Status:** Accepted
**Authors:** ArchiLLM ADR Generator (LLM-assisted from pattern catalogue)
**Date:** 2026-07-23

## Context and Problem Statement
What is the database architecture in a microservices application? Services must be loosely coupled so that they can be developed, deployed and scaled independently. However, some business transactions must enforce invariants that span multiple services, update data owned by multiple services, or query data owned by multiple services. Some queries must join data that is owned by multiple services. Additionally, databases must sometimes be replicated and sharded in order to scale, and different services have different data storage requirements.

## Requirements (Functional & Non-Functional)
- Services must be loosely coupled so that they can be developed, deployed and scaled independently
- Some business transactions must enforce invariants that span multiple services
- Some business transactions must update data owned by multiple services
- Some business transactions need to query data that is owned by multiple services
- Some queries must join data that is owned by multiple services
- Databases must sometimes be replicated and sharded in order to scale
- Different services have different data storage requirements (for some services, a relational database is the best choice; other services might need a NoSQL database such as MongoDB, which is good at storing complex, unstructured data, or Neo4J, which is designed to efficiently store and query graph data)

## Critical User Journey Impacted
- Place Order use case: must verify that a new Order will not exceed the customer's credit limit
- View Available Credit: must query the Customer to find the creditLimit and Orders to calculate the total amount of the open orders
- Finding customers in a particular region and their recent orders: requires a join between customers and orders

## Considered Options
- Shared Database anti-pattern (describes the problems that result from microservices sharing a database)

## Decision and Rationale
Keep each microservice's persistent data private to that service and accessible only via its API. A service's transactions only involve its database. This helps ensure that the services are loosely coupled, and allows each service to use the type of database that is best suited to its needs.

## Consequences
Benefits:
- Helps ensure that the services are loosely coupled. Changes to one service's database does not impact any other services.
- Each service can use the type of database that is best suited to its needs. For example, a service that does text searches could use ElasticSearch. A service that manipulates a social graph could use Neo4j.

Drawbacks:
- Implementing business transactions that span multiple services is not straightforward. Distributed transactions are best avoided because of the CAP theorem. Moreover, many modern (NoSQL) databases don't support them.
- Implementing queries that join data that is now in multiple databases is challenging.
- Complexity of managing multiple SQL and NoSQL databases

Patterns/solutions for implementing transactions and queries that span services:
- Implementing transactions that span services: use the Saga pattern.
- Implementing queries that span services:
  - API Composition: the application performs the join rather than the database. For example, a service (or the API gateway) could retrieve a customer and their orders by first retrieving the customer from the customer service and then querying the order service to return the customer's most recent orders.
  - Command Query Responsibility Segregation (CQRS): maintain one or more materialized views that contain data from multiple services. The views are kept by services that subscribe to events that each services publishes when it updates its data. For example, the online store could implement a query that finds customers in a particular region and their recent orders by maintaining a view that joins customers and orders. The view is updated by a service that subscribes to customer and order events.