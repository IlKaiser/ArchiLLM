# ADR-004: API Composition

**Status:** Accepted
**Authors:** ArchiLLM ADR Generator (LLM-assisted from pattern catalogue)
**Date:** 2026-07-23

## Context and Problem Statement
We have applied the Microservices architecture pattern and the Database per service pattern. As a result, it is no longer straightforward to implement queries that join data from multiple services. The problem to be solved is: how to implement queries in a microservice architecture?

## Requirements (Functional & Non-Functional)
No explicit forces or constraints were listed in the API Composition section of the source text.

## Critical User Journey Impacted
Building an online store product details page that must display information spread across multiple services (Product Info Service, Pricing Service, Order Service, Inventory Service, Review Service, etc.), requiring the code to fetch information from all of these services. The page must support multiple client types including HTML5/JavaScript-based UI for desktop and mobile browsers, native Android and iPhone clients, and 3rd party applications via REST API.

## Considered Options
No alternative patterns were mentioned in the source text.

## Decision and Rationale
We will implement queries by defining an API Composer, which invokes the services that own the data and performs an in-memory join of the results. This solution addresses the challenge of implementing queries that span multiple services when using the Database per service pattern.

## Consequences
No benefits or drawbacks were specified in the source text's Resulting context section.