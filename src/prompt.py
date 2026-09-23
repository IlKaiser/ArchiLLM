#- `dataset/student_projects/{title}/input.txt` — system description and user stories

DIAGRAM_EXTRACT_PROMPT = """
## Task
Analyze the dataset input for project `{title}` and extract its complete microservices architecture as a structured JSON file.

## Working Directory
Your workspace is: `{workspace_dir}`
All file paths below are relative to this directory. Use the exact absolute path `{workspace_dir}/architecture.json` when writing output.

## Input Files
Read the following file:
- `{workspace_dir}/input.txt` — system description and user stories

## Extraction Guidelines
From the input files, extract:

**Microservices** — small, focused services with clear responsibilities. For each:
- `name`: short snake_case identifier
- `description`: what the service is responsible for
- `user_stories`: list of user story IDs this service implements

**Patterns** — architectural patterns (allowed: database per service, api composition, cqrs, saga, aggregate, event sourcing, domain event). For each:
- `group_name`: a meaningful name for the group
- `implementation_pattern`: the pattern identifier (lowercase)
- `involved_microservices`: list of service names in this group
- `explanation`: rationale for choosing this pattern

**Datastores** — persistent storage each service requires. For each:
- `datastore_name`: a meaningful name
- `associated_microservice`: the owning service name
- `type`: one of relational, document, cache, event_store
- `description`: what data is stored and which user stories drove this choice

**Dependencies** — how services communicate. For each:
- `from`: calling service name
- `to`: called service name
- `protocol`: one of REST, WebSocket, event, gRPC
- `description`: what data flows and why

## Output
Save the extracted architecture as `{workspace_dir}/architecture.json`, following the schema above.

## Architectural Knowledge Base
Use the following pattern catalogue as reference when identifying and assigning architectural patterns. Always prefer patterns from this catalogue and follow their prescribed forces, solutions, and trade-offs:

{knowledge_base}

## Constraints
- DO NOT generate any implementation code.
- DO NOT generate any diagrams.
- Only read the input files, reason about the architecture, and save the JSON.
{extra_instructions}"""

DIAGRAM_RENDER_PROMPT = """
## Task
Generate a UML component microservice diagram and a written architecture summary for project `{title}`.

## Working Directory
Your workspace is: `{workspace_dir}`
All file paths below are relative to this directory. Use exact absolute paths when reading and writing.

## Input
Read the extracted architecture from: `{workspace_dir}/architecture.json`

## Output 1 — PlantUML Component Diagram (`component_diagram.puml`)
Generate a valid PlantUML component diagram following these rules:
- Every microservice → a `[Component]` element with a readable quoted label
- Every datastore → a `database` element placed directly next to its owning service and connected with a plain `--` line (no label). Use the syntax: `[service_alias] -- database_alias`
- Each database MUST be defined inside the same package/frame block as its owning service so the ownership is visually explicit
- Every inter-service dependency → a directed arrow labelled with the protocol (REST, WebSocket, event, gRPC)
- Microservices sharing the same architectural pattern → grouped inside a `package` or `frame` block named after the pattern
- Each component must be defined ONCE (in its primary pattern package). If a component participates in multiple patterns, define it only in one package and add a note or comment — do NOT duplicate the definition
- Use snake_case aliases for PlantUML identifiers; use readable quoted strings as display labels
- Include a `legend` block explaining arrow and notation conventions
- The file must start with `@startuml` and end with `@enduml`

## Output 2 — Architecture Summary (`architecture_summary.md`)
Generate a Markdown document containing:
1. A table of all microservices: name | description | user stories
2. A table of all architectural patterns: group name | pattern | involved services | rationale
3. A table of all datastores: name | type | owning service | description
4. A table of all inter-service dependencies: from | to | protocol | description

## Architectural Knowledge Base
Use the following pattern catalogue when grouping microservices into packages and verifying that inter-service dependencies follow correct protocols and rationales:

{knowledge_base}

## Constraints
- DO NOT generate any implementation code.
- Output only two files: `{workspace_dir}/component_diagram.puml` and `{workspace_dir}/architecture_summary.md`.
- The PlantUML must be syntactically valid.
{extra_instructions}"""

DIAGRAM_VALIDATE_PROMPT = """
## Task
Validate the generated microservices architecture for project `{title}` against the ground-truth dataset metrics.

## Input Files
Read ALL of the following files before proceeding:
- `dataset/student_projects/{title}/DataMetrics.json` — ground-truth groupings: each entry has `set_id`, `set_name`, `user_stories` (list of IDs covered), `links` (set_ids this set communicates with), and `db` (bool — whether this group needs a datastore)
- `run/{title}/architecture.json` — extracted architecture (microservices, patterns, datastores, dependencies)
- `run/{title}/component_diagram.puml` — generated PlantUML diagram

## Validation Checks
For each entry in DataMetrics.json, verify:

1. **Coverage** — every `set_name` group maps to at least one microservice in architecture.json. Report which sets are missing or only partially covered.
2. **User Story Mapping** — the user stories listed under each set appear in at least one microservice's `user_stories` field. Report any uncovered user story IDs.
3. **Inter-Service Links** — each `links` relationship (set A ↔ set B) corresponds to at least one dependency in architecture.json. Report any missing or extra dependencies.
4. **Datastore Presence** — every set with `"db": true` has at least one associated datastore in architecture.json. Report any sets with `db: true` that lack a datastore.
5. **Diagram Completeness** — every microservice in architecture.json appears as a component in the PlantUML diagram. Report any missing components.

## Output — `run/{title}/validation_report.md`
Write a Markdown report structured as follows:

```
# Validation Report — {title}

## Summary
| Check | Status | Issues |
|---|---|---|
| Coverage | PASS/FAIL | N issues |
| User Story Mapping | PASS/FAIL | N issues |
| Inter-Service Links | PASS/FAIL | N issues |
| Datastore Presence | PASS/FAIL | N issues |
| Diagram Completeness | PASS/FAIL | N issues |

## Details
[One subsection per failed check listing each specific issue]

## Overall
PASS / FAIL (X of 5 checks passed)
```

## Constraints
- DO NOT modify any existing files.
- Output only `validation_report.md`.
- Be precise: cite exact set names, service names, and user story IDs in every issue.
"""


KNOWLEDGE_BASE = """
# Patterns

## Pattern: Database per service (MANDATORY for all microservices)

### Problem
What’s the database architecture in a microservices application?

### Forces
Services must be loosely coupled so that they can be developed, deployed and scaled independently

Some business transactions must enforce invariants that span multiple services. For example, the Place Order use case must verify that a new Order will not exceed the customer’s credit limit. Other business transactions, must update data owned by multiple services.

Some business transactions need to query data that is owned by multiple services. For example, the View Available Credit use must query the Customer to find the creditLimit and Orders to calculate the total amount of the open orders.

Some queries must join data that is owned by multiple services. For example, finding customers in a particular region and their recent orders requires a join between customers and orders.

Databases must sometimes be replicated and sharded in order to scale. See the Scale Cube.

Different services have different data storage requirements. For some services, a relational database is the best choice. Other services might need a NoSQL database such as MongoDB, which is good at storing complex, unstructured data, or Neo4J, which is designed to efficiently store and query graph data.

### Solution
Keep each microservice’s persistent data private to that service and accessible only via its API. A service’s transactions only involve its database.

### Resulting context
Using a database per service has the following benefits:

Helps ensure that the services are loosely coupled. Changes to one service’s database does not impact any other services.

Each service can use the type of database that is best suited to its needs. For example, a service that does text searches could use ElasticSearch. A service that manipulates a social graph could use Neo4j.

Using a database per service has the following drawbacks:

Implementing business transactions that span multiple services is not straightforward. Distributed transactions are best avoided because of the CAP theorem. Moreover, many modern (NoSQL) databases don’t support them.

Implementing queries that join data that is now in multiple databases is challenging.

Complexity of managing multiple SQL and NoSQL databases

There are various patterns/solutions for implementing transactions and queries that span services:

Implementing transactions that span services - use the Saga pattern.

Implementing queries that span services:

API Composition - the application performs the join rather than the database. For example, a service (or the API gateway) could retrieve a customer and their orders by first retrieving the customer from the customer service and then querying the order service to return the customer’s most recent orders.

Command Query Responsibility Segregation (CQRS) - maintain one or more materialized views that contain data from multiple services. The views are kept by services that subscribe to events that each services publishes when it updates its data. For example, the online store could implement a query that finds customers in a particular region and their recent orders by maintaining a view that joins customers and orders. The view is updated by a service that subscribes to customer and order events.

### Related patterns
Microservice architecture pattern creates the need for this pattern
Saga pattern is a useful way to implement eventually consistent transactions
The API Composition and Command Query Responsibility Segregation (CQRS) pattern are useful ways to implement queries
The Shared Database anti-pattern describes the problems that result from microservices sharing a database

## Pattern: Saga

### Context
You have applied the Database per Service pattern. Each service has its own database. Some business transactions, however, span multiple service so you need a mechanism to implement transactions that span services. For example, let’s imagine that you are building an e-commerce store where customers have a credit limit. The application must ensure that a new order will not exceed the customer’s credit limit. Since Orders and Customers are in different databases owned by different services the application cannot simply use a local ACID transaction.

### Problem
How to implement transactions that span services?

### Forces
2PC is not an option

### Solution
Implement each business transaction that spans multiple services as a saga. A saga is a sequence of local transactions. Each local transaction updates the database and publishes a message or event to trigger the next local transaction in the saga. If a local transaction fails because it violates a business rule then the saga executes a series of compensating transactions that undo the changes that were made by the preceding local transactions.

### Resulting context
This pattern has the following benefits:

It enables an application to maintain data consistency across multiple services without using distributed transactions
This solution has the following drawbacks:

Lack of automatic rollback - a developer must design compensating transactions that explicitly undo changes made earlier in a saga rather than relying on the automatic rollback feature of ACID transactions

Lack of isolation (the “I” in ACID) - the lack of isolation means that there’s risk that the concurrent execution of multiple sagas and transactions can use data anomalies. consequently, a saga developer must typical use countermeasures, which are design techniques that implement isolation. Moreover, careful analysis is needed to select and correctly implement the countermeasures. See Chapter 4/section 4.3 of my book Microservices Patterns for more information.

There are also the following issues to address:

In order to be reliable, a service must atomically update its database and publish a message/event. It cannot use the traditional mechanism of a distributed transaction that spans the database and the message broker. Instead, it must use one of the patterns listed below.

A client that initiates the saga, which an asynchronous flow, using a synchronous request (e.g. HTTP POST /orders) needs to be able to determine its outcome. There are several options, each with different trade-offs:

The service sends back a response once the saga completes, e.g. once it receives an OrderApproved or OrderRejected event.
The service sends back a response (e.g. containing the orderID) after initiating the saga and the client periodically polls (e.g. GET /orders/{orderID}) to determine the outcome
The service sends back a response (e.g. containing the orderID) after initiating the saga, and then sends an event (e.g. websocket, web hook, etc) to the client once the saga completes.

### Related patterns
The Database per Service pattern creates the need for this pattern
The following patterns are ways to atomically update state and publish messages/events:
Event sourcing
Transactional Outbox
A choreography-based saga can publish events using Aggregates and Domain Events
The Command-side replica is an alternative pattern, which can replace saga step that query data

## Pattern: Command-side replica

### Context
You have applied the Microservices architecture pattern and the Database per service pattern. As a result, a service that implements a system command often needs to query other services. For example, the createOrder() command is implemented by the Order Service, which needs to retrieve the restaurant’s menu Restaurant Service in order to price and validate the line items.

One option is for the Order Service to query the Restaurant Service each time. The query can either be implemented synchronously using, for example, or asynchronously as a saga step. However, this approach has several drawbacks, which can be partially mitigated by caching, including more network traffic and a runtime dependency on the Restaurant Service.

An alternative approach is to replica the restaurants’ menus to the Order Service.

### Problem
How can a service that implements a command retrieve data from another service?

There are five dark energy forces:

Simple components - simple components consisting of few subdomains are easier to understand and maintain than complex components
Team autonomy - a team needs to be able to develop, test and deploy their software independently of other teams
Fast deployment pipeline - fast feedback and high deployment frequency are essential and are enabled by a fast deployment pipeline, which in turn requires components that are fast to build and test.
Support multiple technology stacks - subdomains are sometimes implemented using a variety of technologies; and developers need to evolve the application’s technology stack, e.g. use current versions of languages and frameworks
Segregate by characteristics - e.g. resource requirements to improve scalability, their availability requirements to improve availability, their security requirements to improve security, etc.
There are five dark matter forces:

Simple interactions - an operation that’s local to a component or consists of a few simple interactions between components is easier to understand and troubleshoot than a distributed operation, especially one consisting of complex interactions
Efficient interactions - a distributed operation that involves lots of network round trips and large data transfers can be too inefficient
Prefer ACID over BASE - it’s easier to implement an operation as an ACID transaction rather than, for example, eventually consistent sagas
Minimize runtime coupling - to maximize the availability and reduce the latency of an operation
Minimize design time coupling - reduce the likelihood of changing services in lockstep, which reduces productivity

### Solution
The solution consists of the following elements:

Command service - the service that implements the command.
Provider service - the service that owns the data that the command service needs
Replica database - a read-only replica of the data from the provider service. The command service keeps the replica up to data by subscribing to Domain events published by the provider service

### Resulting context
#### Benefits
This pattern resolves the following forces:

Support multiple technology stacks - the replica database can use a technology stack that’s more optimized to support the command
Segregate by characteristics - the provider service is no longer invoked by the command and so might need to be as performant or available
Simple interactions - the command is simpler since it no longer needs to interact with the provider service
Efficient interactions - the command is more efficient since it no longer needs to interact with the provider service
Prefer ACID over BASE - the replica is potentially stale
Minimize runtime coupling - runtime coupling is reduced since the the command no longer needs to interact with the provider service
#### Drawbacks
This pattern potentially fails to resolve the following forces:

Simple components - makes the command service more complicated since it needs to maintain the replica. It also complicates the provider service since it must publish the events.
Team autonomy - the provider service’s team might need to coordinate more frequently with command service team due to increased design-time coupling (see below)
Fast deployment pipeline - the command service’s deployment pipeline might be slower since it needs test the replica
Segregate by characteristics - potentially increased since, for example, if the replica database contains regulated data (e.g. PII) then the command service might be more complicated.
Simple interactions - potentially more complicated since the provider service’s commands must publish events
Efficient interactions - potentially less efficient since the provider service might publish a large volume of events
Minimize design-time coupling - risk of tight design-time coupling between services, since the command service needs to know about the structure of the data that is replicated and potentially its lifecycle events.

### Related patterns
The Database per Service pattern creates the need for this pattern
The Saga is an alternative solution
The Domain event pattern generates the events
This pattern is structurally identical to CQRS.

## Pattern: API Composition

### Context
You have applied the Microservices architecture pattern and the Database per service pattern. As a result, it is no longer straightforward to implement queries that join data from multiple services.

### Problem
How to implement queries in a microservice architecture?

### Solution
Implement a query by defining an API Composer, which invoking the services that own the data and performs an in-memory join of the results.

### API Gateway
#### Context
Let’s imagine you are building an online store that uses the Microservice architecture pattern and that you are implementing the product details page. You need to develop multiple versions of the product details user interface:

HTML5/JavaScript-based UI for desktop and mobile browsers - HTML is generated by a server-side web application
Native Android and iPhone clients - these clients interact with the server via REST APIs
In addition, the online store must expose product details via a REST API for use by 3rd party applications.

A product details UI can display a lot of information about a product. For example, the Amazon.com details page for POJOs in Action displays:

Basic information about the book such as title, author, price, etc.
Your purchase history for the book
Availability
Buying options
Other items that are frequently bought with this book
Other items bought by customers who bought this book
Customer reviews
Sellers ranking
…
Since the online store uses the Microservice architecture pattern the product details data is spread over multiple services. For example,

Product Info Service - basic information about the product such as title, author
Pricing Service - product price
Order service - purchase history for product
Inventory service - product availability
Review service - customer reviews …
Consequently, the code that displays the product details needs to fetch information from all of these services.

#### Problem
How do the clients of a Microservices-based application access the individual services?

#### Forces
The granularity of APIs provided by microservices is often different than what a client needs. Microservices typically provide fine-grained APIs, which means that clients need to interact with multiple services. For example, as described above, a client needing the details for a product needs to fetch data from numerous services.

Different clients need different data. For example, the desktop browser version of a product details page desktop is typically more elaborate then the mobile version.

Network performance is different for different types of clients. For example, a mobile network is typically much slower and has much higher latency than a non-mobile network. And, of course, any WAN is much slower than a LAN. This means that a native mobile client uses a network that has very difference performance characteristics than a LAN used by a server-side web application. The server-side web application can make multiple requests to backend services without impacting the user experience where as a mobile client can only make a few.

The number of service instances and their locations (host+port) changes dynamically

Partitioning into services can change over time and should be hidden from clients

Services might use a diverse set of protocols, some of which might not be web friendly

#### Solution
Implement an API gateway that is the single entry point for all clients. The API gateway handles requests in one of two ways. Some requests are simply proxied/routed to the appropriate service. It handles other requests by fanning out to multiple services.


## Pattern: Command Query Responsibility Segregation (CQRS)
### Context
You have applied the Microservices architecture pattern and the Database per service pattern. As a result, it is no longer straightforward to implement queries that join data from multiple services. Also, if you have applied the Event sourcing pattern then the data is no longer easily queried.

### Problem
How to implement a query that retrieves data from multiple services in a microservice architecture?

### Solution
Define a view database, which is a read-only ‘replica’ that is designed specifically to support that query, or a group related queries. The application keeps the database up to date by subscribing to Domain events published by the service that own the data. The type of database and its schema are optimized for the query or queries. It’s often a NoSQL database, such as a document database or a key-value store.

### Resulting context
This pattern has the following benefits:

Supports multiple denormalized views that are scalable and performant
Improved separation of concerns = simpler command and query models
Necessary in an event sourced architecture

This pattern has the following drawbacks:

Increased complexity
Potential code duplication
Replication lag/eventually consistent views

### Related patterns
The Database per Service pattern creates the need for this pattern
The API Composition pattern is an alternative solution
The Domain event pattern generates the events
CQRS is often used with Event sourcing

## Pattern: Domain event
### Context
A service often needs to publish events when it updates its data. These events might be needed, for example, to update a CQRS view. Alternatively, the service might participate in an choreography-based saga, which uses events for coordination.

### Problem
How does a service publish an event when it updates its data?

### Solution
Organize the business logic of a service as a collection of DDD aggregates that emit domain events when they created or updated. The service publishes these domain events so that they can be consumed by other services.

### Related patterns
The Saga and CQRS patterns create the need for this pattern
The Aggregate pattern is used to structure the business logic
The Transactional outbox pattern is used to publish events as part of a database transaction
Event sourcing is sometimes used to publish domain events

## Pattern: Event sourcing
### Context
A service command typically needs to create/update/delete aggregates in the database and send messages/events to a message broker. For example, a service that participates in a saga needs to update business entities and send messages/events. Similarly, a service that publishes a domain event must update an aggregate and publish an event.

The command must atomically update the database and send messages in order to avoid data inconsistencies and bugs. However, it is not viable to use a traditional distributed transaction (2PC) that spans the database and the message broker The database and/or the message broker might not support 2PC. And even if they do, it’s often undesirable to couple the service to both the database and the message broker.

But without using 2PC, sending a message in the middle of a transaction is not reliable. There’s no guarantee that the transaction will commit. Similarly, if a service sends a message after committing the transaction there’s no guarantee that it won’t crash before sending the message.

In addition, messages must be sent to the message broker in the order they were sent by the service. They must usually be delivered to each consumer in the same order although that’s outside the scope of this pattern. For example, let’s suppose that an aggregate is updated by a series of transactions T1, T2, etc. This transactions might be performed by the same service instance or by different service instances. Each transaction publishes a corresponding event: T1 -> E1, T2 -> E2, etc. Since T1 precedes T2, event E1 must be published before E2.

### Problem
How to atomically update the database and send messages to a message broker?

### Forces
2PC is not an option. The database and/or the message broker might not support 2PC. Also, it’s often undesirable to couple the service to both the database and the message broker.
If the database transaction commits then the messages must be sent. Conversely, if the database rolls back, the messages must not be sent
Messages must be sent to the message broker in the order they were sent by the service. This ordering must be preserved across multiple service instances that update the same aggregate.

### Solution
A good solution to this problem is to use event sourcing. Event sourcing persists the state of a business entity such an Order or a Customer as a sequence of state-changing events. Whenever the state of a business entity changes, a new event is appended to the list of events. Since saving an event is a single operation, it is inherently atomic. The application reconstructs an entity’s current state by replaying the events.

Applications persist events in an event store, which is a database of events. The store has an API for adding and retrieving an entity’s events. The event store also behaves like a message broker. It provides an API that enables services to subscribe to events. When a service saves an event in the event store, it is delivered to all interested subscribers.

Some entities, such as a Customer, can have a large number of events. In order to optimize loading, an application can periodically save a snapshot of an entity’s current state. To reconstruct the current state, the application finds the most recent snapshot and the events that have occurred since that snapshot. As a result, there are fewer events to replay.

### Resulting context
Event sourcing has several benefits:

It solves one of the key problems in implementing an event-driven architecture and makes it possible to reliably publish events whenever state changes.
Because it persists events rather than domain objects, it mostly avoids the object‑relational impedance mismatch problem.
It provides a 100% reliable audit log of the changes made to a business entity
It makes it possible to implement temporal queries that determine the state of an entity at any point in time.
Event sourcing-based business logic consists of loosely coupled business entities that exchange events. This makes it a lot easier to migrate from a monolithic application to a microservice architecture.
Event sourcing also has several drawbacks:

It is a different and unfamiliar style of programming and so there is a learning curve.
The event store is difficult to query since it requires typical queries to reconstruct the state of the business entities. That is likely to be complex and inefficient. As a result, the application must use Command Query Responsibility Segregation (CQRS) to implement queries. This in turn means that applications must handle eventually consistent data.

### Related patterns
The Saga and Domain event patterns create the need for this pattern.
The CQRS must often be used with event sourcing.
Event sourcing implements the Audit logging pattern.
"""

DIAGRAM_SYNTAX_FIX_PROMPT = """
## Task
The PlantUML file `{workspace_dir}/component_diagram.puml` has syntax errors that must be corrected.

## Detected Issues
{issues}

## Instructions
1. Read the file `{workspace_dir}/component_diagram.puml`.
2. Fix ALL the syntax issues listed above while preserving the architecture and semantics of the diagram.
3. Common PlantUML fixes:
   - Ensure the file starts with `@startuml` and ends with `@enduml`
   - Balance all curly braces `{{` `}}`
   - Balance all square brackets `[` `]`
   - Close all open double-quotes
   - Remove any invalid arrow syntax (valid: `-->`, `..>`, `--`, `..`, `->`, `.>`)
   - Ensure every `package`, `frame`, `node`, or `rectangle` block has a matching closing `}}`
   - Remove duplicate or conflicting alias definitions
4. Save the corrected file back to `{workspace_dir}/component_diagram.puml`.

## Constraints
- DO NOT change the architecture, component names, relationships, or groupings.
- ONLY fix syntax so the diagram compiles without errors.
"""


class DiagramPrompt:
    def __init__(self, title: str):
        self.title = title

    def get_extract_prompt(self, workspace_dir: str, extra_instructions: str = "") -> str:
        return DIAGRAM_EXTRACT_PROMPT.format(
            title=self.title,
            knowledge_base=KNOWLEDGE_BASE,
            workspace_dir=workspace_dir,
            extra_instructions=extra_instructions,
        )

    def get_render_prompt(self, workspace_dir: str, extra_instructions: str = "") -> str:
        return DIAGRAM_RENDER_PROMPT.format(
            title=self.title,
            knowledge_base=KNOWLEDGE_BASE,
            workspace_dir=workspace_dir,
            extra_instructions=extra_instructions,
        )

    def get_validate_prompt(self) -> str:
        return DIAGRAM_VALIDATE_PROMPT.format(title=self.title)

    def get_syntax_fix_prompt(self, issues: str, workspace_dir: str) -> str:
        return DIAGRAM_SYNTAX_FIX_PROMPT.format(title=self.title, issues=issues, workspace_dir=workspace_dir)


