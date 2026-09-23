# ADR-003: Command-side replica

**Status:** Accepted
**Authors:** ArchiLLM ADR Generator (LLM-assisted from pattern catalogue)
**Date:** 2026-07-23

## Context and Problem Statement
You have applied the Microservices architecture pattern and the Database per service pattern. As a result, a service that implements a system command often needs to query other services. One option is for the service to query the other service each time, either synchronously or asynchronously as a saga step, but this approach has drawbacks including more network traffic and a runtime dependency on the other service, which can be partially mitigated by caching.

The problem is: How can a service that implements a command retrieve data from another service?

## Requirements (Functional & Non-Functional)
- Simple components - simple components consisting of few subdomains are easier to understand and maintain than complex components
- Team autonomy - a team needs to be able to develop, test and deploy their software independently of other teams
- Fast deployment pipeline - fast feedback and high deployment frequency are essential and are enabled by a fast deployment pipeline, which in turn requires components that are fast to build and test
- Support multiple technology stacks - subdomains are sometimes implemented using a variety of technologies; and developers need to evolve the application's technology stack, e.g. use current versions of languages and frameworks
- Segregate by characteristics - e.g. resource requirements to improve scalability, their availability requirements to improve availability, their security requirements to improve security, etc.
- Simple interactions - an operation that's local to a component or consists of a few simple interactions between components is easier to understand and troubleshoot than a distributed operation, especially one consisting of complex interactions
- Efficient interactions - a distributed operation that involves lots of network round trips and large data transfers can be too inefficient
- Prefer ACID over BASE - it's easier to implement an operation as an ACID transaction rather than, for example, eventually consistent sagas
- Minimize runtime coupling - to maximize the availability and reduce the latency of an operation
- Minimize design time coupling - reduce the likelihood of changing services in lockstep, which reduces productivity

## Critical User Journey Impacted
The createOrder() command is implemented by the Order Service, which needs to retrieve the restaurant's menu from the Restaurant Service in order to price and validate the line items.

## Considered Options
- Querying the provider service each time, implemented either synchronously or asynchronously as a saga step (with caching as a partial mitigation for drawbacks)
- Saga (as an alternative solution)

## Decision and Rationale
Adopt the Command-side replica pattern, which consists of the following elements:
- **Command service**: the service that implements the command
- **Provider service**: the service that owns the data that the command service needs
- **Replica database**: a read-only replica of the data from the provider service. The command service keeps the replica up to data by subscribing to Domain events published by the provider service

This pattern resolves the forces of Support multiple technology stacks (the replica database can use a technology stack that's more optimized to support the command), Segregate by characteristics (the provider service is no longer invoked by the command and so might not need to be as performant or available), Simple interactions (the command is simpler since it no longer needs to interact with the provider service), Efficient interactions (the command is more efficient since it no longer needs to interact with the provider service), Minimize runtime coupling (runtime coupling is reduced since the command no longer needs to interact with the provider service), and Prefer ACID over BASE (the replica is potentially stale).

## Consequences

### Benefits
- **Support multiple technology stacks**: the replica database can use a technology stack that's more optimized to support the command
- **Segregate by characteristics**: the provider service is no longer invoked by the command and so might not need to be as performant or available
- **Simple interactions**: the command is simpler since it no longer needs to interact with the provider service
- **Efficient interactions**: the command is more efficient since it no longer needs to interact with the provider service
- **Prefer ACID over BASE**: the replica is potentially stale
- **Minimize runtime coupling**: runtime coupling is reduced since the command no longer needs to interact with the provider service

### Drawbacks
- **Simple components**: makes the command service more complicated since it needs to maintain the replica. It also complicates the provider service since it must publish the events.
- **Team autonomy**: the provider service's team might need to coordinate more frequently with command service team due to increased design-time coupling
- **Fast deployment pipeline**: the command service's deployment pipeline might be slower since it needs test the replica
- **Segregate by characteristics**: potentially increased since, for example, if the replica database contains regulated data (e.g. PII) then the command service might be more complicated.
- **Simple interactions**: potentially more complicated since the provider service's commands must publish events
- **Efficient interactions**: potentially less efficient since the provider service might publish a large volume of events
- **Minimize design-time coupling**: risk of tight design-time coupling between services, since the command service needs to know about the structure of the data that is replicated and potentially its lifecycle events.