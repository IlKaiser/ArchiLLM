# ADR-005: Command Query Responsibility Segregation (CQRS)

**Status:** Accepted
**Authors:** ArchiLLM ADR Generator (LLM-assisted from pattern catalogue)
**Date:** 2026-07-23

## Context and Problem Statement
You have applied the Microservices architecture pattern and the Database per service pattern. As a result, it is no longer straightforward to implement queries that join data from multiple services. Also, if you have applied the Event sourcing pattern then the data is no longer easily queried.

The problem is: How to implement a query that retrieves data from multiple services in a microservice architecture?

## Requirements (Functional & Non-Functional)
- Must implement queries that retrieve data from multiple services where the Database per service pattern prevents straightforward joins
- Must support querying when the Event sourcing pattern is applied and data is no longer easily queried

## Critical User Journey Impacted
No concrete example scenario was given in the source.

## Considered Options
- **API Composition pattern**: An alternative solution to implement queries across multiple services.

## Decision and Rationale
Define a view database, which is a read-only 'replica' that is designed specifically to support that query, or a group related queries. The application keeps the database up to date by subscribing to Domain events published by the service that own the data. The type of database and its schema are optimized for the query or queries. It's often a NoSQL database, such as a document database or a key-value store.

This resolves the stated problem by providing a dedicated, query-optimized read model that aggregates data from multiple services via domain events, bypassing the need for complex joins across service boundaries or direct querying of event stores.

## Consequences
**Benefits:**
- Supports multiple denormalized views that are scalable and performant
- Improved separation of concerns = simpler command and query models
- Necessary in an event sourced architecture

**Drawbacks:**
- Increased complexity
- Potential code duplication
- Replication lag/eventually consistent views