# ADR-006: Domain event

**Status:** Accepted
**Authors:** ArchiLLM ADR Generator (LLM-assisted from pattern catalogue)
**Date:** 2026-07-23

## Context and Problem Statement
A service often needs to publish events when it updates its data. These events might be needed, for example, to update a CQRS view. Alternatively, the service might participate in an choreography-based saga, which uses events for coordination.

The problem is: How does a service publish an event when it updates its data?

## Requirements (Functional & Non-Functional)
- Support publishing events when a service updates its data
- Support consumption of events by other services to update CQRS views
- Support participation in choreography-based sagas using events for coordination
- Structure business logic using DDD aggregates that emit domain events when created or updated

## Critical User Journey Impacted
- Updating a CQRS view using events published when data is updated
- Participating in a choreography-based saga which uses events for coordination

## Considered Options
- **Transactional outbox pattern**: Used to publish events as part of a database transaction
- **Event sourcing**: Sometimes used to publish domain events
- **Aggregate pattern**: Used to structure the business logic
- **Saga pattern**: Creates the need for this pattern
- **CQRS pattern**: Creates the need for this pattern

## Decision and Rationale
**Decision:** Organize the business logic of a service as a collection of DDD aggregates that emit domain events when they created or updated. The service publishes these domain events so that they can be consumed by other services.

**Rationale:** This approach enables the service to publish events whenever it updates its data, satisfying the requirements for CQRS view updates and choreography-based saga coordination.

## Consequences
No benefits or drawbacks were specified in the source text.