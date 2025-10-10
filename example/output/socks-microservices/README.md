# Socks Microservices (Spring Boot)

Multi-module Maven workspace with 9 modules:
- `common` (shared events)
- `catalog-service` (8081)
- `cart-service` (8082)
- `checkout-service` (8083)
- `order-service` (8084)
- `shipping-service` (8085)
- `rating-service` (8086)
- `logging-service` (8087)
- `monitoring-service` (8088)

## Build
```bash
mvn -q -DskipTests package
```

## Run (example)
```bash
mvn -q -pl catalog-service spring-boot:run
mvn -q -pl cart-service spring-boot:run
# ... etc for each module
```

## Sample Requests
See the conversation for example payloads. All services use in-memory stores.
