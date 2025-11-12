package com.example.order.domain;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

// Domain event base class
abstract class OrderDomainEvent {}

// Example event
class OrderCreatedEvent extends OrderDomainEvent {
    private final Long orderId;
    private final Long consumerId;
    private final Long restaurantId;
    private final List<OrderLineItem> lineItems;
    private final BigDecimal orderTotal;

    public OrderCreatedEvent(Long orderId, Long consumerId, Long restaurantId, List<OrderLineItem> lineItems, BigDecimal orderTotal) {
        this.orderId = orderId;
        this.consumerId = consumerId;
        this.restaurantId = restaurantId;
        this.lineItems = lineItems;
        this.orderTotal = orderTotal;
    }

    public Long getOrderId() {
        return orderId;
    }

    public Long getConsumerId() {
        return consumerId;
    }

    public Long getRestaurantId() {
        return restaurantId;
    }

    public List<OrderLineItem> getLineItems() {
        return lineItems;
    }

    public BigDecimal getOrderTotal() {
        return orderTotal;
    }
}

// Value object for line items
class OrderLineItem {
    private final String menuItemId;
    private final String name;
    private final BigDecimal price;
    private final int quantity;

    public OrderLineItem(String menuItemId, String name, BigDecimal price, int quantity) {
        this.menuItemId = menuItemId;
        this.name = name;
        this.price = price;
        this.quantity = quantity;
    }

    public String getMenuItemId() {
        return menuItemId;
    }

    public String getName() {
        return name;
    }

    public BigDecimal getPrice() {
        return price;
    }

    public int getQuantity() {
        return quantity;
    }
}

// Aggregate root
public class Order {

    public enum State {
        APPROVAL_PENDING, APPROVED, REJECTED, CANCELLED
    }

    private Long id;
    private Long consumerId;
    private Long restaurantId;
    private List<OrderLineItem> lineItems;
    private BigDecimal orderTotal;
    private State state;
    private Instant createdAt;

    // For JPA or serialization
    protected Order() {}

    private Order(Long consumerId, Long restaurantId, List<OrderLineItem> lineItems) {
        this.consumerId = consumerId;
        this.restaurantId = restaurantId;
        this.lineItems = new ArrayList<>(lineItems);
        this.orderTotal = calculateOrderTotal(lineItems);
        this.state = State.APPROVAL_PENDING;
        this.createdAt = Instant.now();
    }

    public static ResultWithDomainEvents<Order, OrderDomainEvent> createOrder(Long consumerId, Long restaurantId, List<OrderLineItem> lineItems) {
        Order order = new Order(consumerId, restaurantId, lineItems);
        OrderCreatedEvent event = new OrderCreatedEvent(
                order.getId(),
                consumerId,
                restaurantId,
                Collections.unmodifiableList(lineItems),
                order.getOrderTotal()
        );
        List<OrderDomainEvent> events = Collections.singletonList(event);
        return new ResultWithDomainEvents<>(order, events);
    }

    public Long getId() {
        return id;
    }

    public Long getConsumerId() {
        return consumerId;
    }

    public Long getRestaurantId() {
        return restaurantId;
    }

    public List<OrderLineItem> getLineItems() {
        return Collections.unmodifiableList(lineItems);
    }

    public BigDecimal getOrderTotal() {
        return orderTotal;
    }

    public State getState() {
        return state;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    private BigDecimal calculateOrderTotal(List<OrderLineItem> items) {
        return items.stream()
                .map(li -> li.getPrice().multiply(BigDecimal.valueOf(li.getQuantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    // Example state transition
    public List<OrderDomainEvent> approve() {
        if (state != State.APPROVAL_PENDING) {
            throw new IllegalStateException("Order cannot be approved in state: " + state);
        }
        this.state = State.APPROVED;
        // TODO: Add OrderApprovedEvent
        return Collections.emptyList();
    }

    public List<OrderDomainEvent> reject() {
        if (state != State.APPROVAL_PENDING) {
            throw new IllegalStateException("Order cannot be rejected in state: " + state);
        }
        this.state = State.REJECTED;
        // TODO: Add OrderRejectedEvent
        return Collections.emptyList();
    }

    public List<OrderDomainEvent> cancel() {
        if (state != State.APPROVAL_PENDING && state != State.APPROVED) {
            throw new IllegalStateException("Order cannot be cancelled in state: " + state);
        }
        this.state = State.CANCELLED;
        // TODO: Add OrderCancelledEvent
        return Collections.emptyList();
    }

    // Saga orchestration hooks (stub)
    public void onSagaStepCompleted(String sagaType, String stepName) {
        // TODO: Implement saga step handling
    }

    // API composition helper (stub)
    public static Order composeFromApis(/* TODO: Add parameters for API composition */) {
        // TODO: Compose order from multiple service APIs
        return null;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Order)) return false;
        Order order = (Order) o;
        return Objects.equals(id, order.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}

// Simple result wrapper for aggregate + events
class ResultWithDomainEvents<T, E> {
    public final T result;
    public final List<E> events;

    public ResultWithDomainEvents(T result, List<E> events) {
        this.result = result;
        this.events = events;
    }
}