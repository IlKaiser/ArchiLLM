# ADR-002: Saga

**Status:** Accepted
**Authors:** ArchiLLM ADR Generator (LLM-assisted from pattern catalogue)
**Date:** 2026-07-23

## Context and Problem Statement
We have applied the Database per Service pattern; each service has its own database. Some business transactions, however, span multiple services, requiring a mechanism to implement transactions that span services. For example, in an e-commerce store where customers have a credit limit, the application must ensure that a new order will not exceed the customer's credit limit. Since Orders and Customers are in different databases owned by different services, the application cannot simply use a local ACID transaction. The core problem is: how to implement transactions that span services?

## Requirements (Functional & Non-Functional)
- Must implement transactions that span multiple services
- 2PC (Two-Phase Commit) is not an option

## Critical User Journey Impacted
An e-commerce store where customers have a credit limit: the application must ensure that a new order will not exceed the customer's credit limit when Orders and Customers are in different databases owned by different services.

## Considered Options
- **Event sourcing**: A pattern to atomically update state and publish messages/events
- **Transactional Outbox**: A pattern to atomically update state and publish messages/events
- **Command-side replica**: An alternative pattern that can replace saga steps that query data
- **Aggregates and Domain Events**: Can be used by a choreography-based saga to publish events

## Decision and Rationale
We will implement each business transaction that spans multiple services as a saga. A saga is a sequence of local transactions. Each local transaction updates the database and publishes a message or event to trigger the next local transaction in the saga. If a local transaction fails because it violates a business rule then the saga executes a series of compensating transactions that undo the changes that were made by the preceding local transactions. This approach maintains data consistency across multiple services without using distributed transactions, which is necessary since 2PC is not an option.

## Consequences
**Benefits:**
- It enables an application to maintain data consistency across multiple services without using distributed transactions

**Drawbacks:**
- Lack of automatic rollback - a developer must design compensating transactions that explicitly undo changes made earlier in a saga rather than relying on the automatic rollback feature of ACID transactions
- Lack of isolation (the "I" in ACID) - the lack of isolation means that there's risk that the concurrent execution of multiple sagas and transactions can cause data anomalies; consequently, a saga developer must typically use countermeasures, which are design techniques that implement isolation; moreover, careful analysis is needed to select and correctly implement the countermeasures

**Issues to Address:**
- In order to be reliable, a service must atomically update its database and publish a message/event without using the traditional mechanism of a distributed transaction that spans the database and the message broker; instead, it must use one of the patterns such as Event Sourcing or Transactional Outbox
- A client that initiates the saga, which is an asynchronous flow, using a synchronous request (e.g. HTTP POST /orders) needs to be able to determine its outcome; options include: the service sends back a response once the saga completes (e.g. once it receives an OrderApproved or OrderRejected event); the service sends back a response after initiating the saga and the client periodically polls to determine the outcome; or the service sends back a response after initiating the saga and then sends an event to the client once the saga completes