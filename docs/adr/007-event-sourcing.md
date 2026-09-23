# ADR-007: Event sourcing

**Status:** Accepted
**Authors:** ArchiLLM ADR Generator (LLM-assisted from pattern catalogue)
**Date:** 2026-07-23

## Context and Problem Statement
A service command typically needs to create/update/delete aggregates in the database and send messages/events to a message broker. For example, a service that participates in a saga needs to update business entities and send messages/events, and a service that publishes a domain event must update an aggregate and publish an event. The command must atomically update the database and send messages to avoid data inconsistencies and bugs. However, it is not viable to use a traditional distributed transaction (2PC) that spans the database and the message broker because the database and/or message broker might not support 2PC, and it is often undesirable to couple the service to both. Sending a message in the middle of a transaction is not reliable because there is no guarantee the transaction will commit; conversely, sending after committing risks the service crashing before sending the message. Additionally, messages must be sent to the message broker in the order they were sent by the service, and this ordering must be preserved across multiple service instances that update the same aggregate (e.g., transactions T1, T2 publishing events E1, E2 where T1 precedes T2 requires E1 to be published before E2).

## Requirements (Functional & Non-Functional)
- 2PC is not an option: the database and/or message broker might not support it, and it is undesirable to couple the service to both.
- If the database transaction commits, the messages must be sent; if the database rolls back, the messages must not be sent.
- Messages must be sent to the message broker in the order they were sent by the service, preserved across multiple service instances updating the same aggregate.

## Critical User Journey Impacted
A service participating in a saga updates business entities and sends messages/events, or a service publishing a domain event updates an aggregate and publishes an event. Specifically, when an aggregate is updated by a series of transactions T1, T2, etc. (performed by the same or different service instances), each transaction publishes a corresponding event (T1 -> E1, T2 -> E2, etc.), and since T1 precedes T2, event E1 must be published before E2.

## Considered Options
- **Saga pattern** and **Domain event pattern**: Create the need for this pattern.
- **CQRS**: Must often be used with event sourcing.
- **Audit logging pattern**: Implemented by event sourcing.

## Decision and Rationale
Use event sourcing. Persist the state of a business entity such as an Order or Customer as a sequence of state-changing events. Whenever the state changes, append a new event to the list of events. Since saving an event is a single operation, it is inherently atomic. The application reconstructs an entity's current state by replaying the events. Applications persist events in an event store, which is a database of events. The store has an API for adding and retrieving an entity's events. The event store also behaves like a message broker, providing an API that enables services to subscribe to events. When a service saves an event in the event store, it is delivered to all interested subscribers. For optimization with entities that have a large number of events (e.g., Customer), the application periodically saves a snapshot of the entity's current state; to reconstruct the current state, the application finds the most recent snapshot and the events that have occurred since that snapshot, resulting in fewer events to replay.

## Consequences
**Benefits:**
- Solves one of the key problems in implementing an event-driven architecture and makes it possible to reliably publish events whenever state changes.
- Because it persists events rather than domain objects, it mostly avoids the object-relational impedance mismatch problem.
- Provides a 100% reliable audit log of the changes made to a business entity.
- Makes it possible to implement temporal queries that determine the state of an entity at any point in time.
- Event sourcing-based business logic consists of loosely coupled business entities that exchange events, making it a lot easier to migrate from a monolithic application to a microservice architecture.

**Drawbacks:**
- It is a different and unfamiliar style of programming and so there is a learning curve.
- The event store is difficult to query since it requires typical queries to reconstruct the state of the business entities, which is likely to be complex and inefficient. As a result, the application must use Command Query Responsibility Segregation (CQRS) to implement queries, which in turn means applications must handle eventually consistent data.