package com.example.order.domain;

import org.springframework.data.annotation.Id;
import org.springframework.data.domain.AbstractAggregateRoot;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

// Aggregate root for Order
public class Order extends AbstractAggregateRoot<Order> {

    @Id
    private Long id;

    private Long consumerId;
    private Long restaurantId;
    private OrderState state;
    private List<OrderLineItem> lineItems = new ArrayList<>();
    private BigDecimal orderTotal;

    // For JPA/Aggregate instantiation
    protected Order() {
    }

    public Order(Long consumerId, Long restaurantId, List<OrderLineItem> lineItems) {
        this.consumerId = consumerId;
        this.restaurantId = restaurantId;
        this.lineItems = new ArrayList<>(lineItems);
        this.orderTotal = calculateOrderTotal(lineItems);
        this.state = OrderState.PENDING;
        registerEvent(new OrderCreatedEvent(this.id, this.consumerId, this.restaurantId, this.lineItems, this.orderTotal));
    }

    public static Order create(Long consumerId, Long restaurantId, List<OrderLineItem> lineItems) {
        return new Order(consumerId, restaurantId, lineItems);
    }

    public void approve() {
        if (state != OrderState.PENDING) {
            throw new IllegalStateException("Order cannot be approved in state: " + state);
        }
        this.state = OrderState.APPROVED;
        registerEvent(new OrderApprovedEvent(this.id));
    }

    public void reject() {
        if (state != OrderState.PENDING) {
            throw new IllegalStateException("Order cannot be rejected in state: " + state);
        }
        this.state = OrderState.REJECTED;
        registerEvent(new OrderRejectedEvent(this.id));
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

    public OrderState getState() {
        return state;
    }

    private BigDecimal calculateOrderTotal(List<OrderLineItem> items) {
        return items.stream()
                .map(OrderLineItem::getTotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    // TODO: Add JPA annotations and mapping if using JPA

    // TODO: Add event publishing integration

    // --- Domain Events ---

    public static class OrderCreatedEvent {
        private final Long orderId;
        private final Long consumerId;
        private final Long restaurantId;
        private final List<OrderLineItem> lineItems;
        private final BigDecimal orderTotal;

        public OrderCreatedEvent(Long orderId, Long consumerId, Long restaurantId, List<OrderLineItem> lineItems, BigDecimal orderTotal) {
            this.orderId = orderId;
            this.consumerId = consumerId;
            this.restaurantId = restaurantId;
            this.lineItems = new ArrayList<>(lineItems);
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
            return Collections.unmodifiableList(lineItems);
        }

        public BigDecimal getOrderTotal() {
            return orderTotal;
        }
    }

    public static class OrderApprovedEvent {
        private final Long orderId;

        public OrderApprovedEvent(Long orderId) {
            this.orderId = orderId;
        }

        public Long getOrderId() {
            return orderId;
        }
    }

    public static class OrderRejectedEvent {
        private final Long orderId;

        public OrderRejectedEvent(Long orderId) {
            this.orderId = orderId;
        }

        public Long getOrderId() {
            return orderId;
        }
    }

    // --- Value Objects ---

    public static class OrderLineItem {
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

        public BigDecimal getTotal() {
            return price.multiply(BigDecimal.valueOf(quantity));
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof OrderLineItem)) return false;
            OrderLineItem that = (OrderLineItem) o;
            return quantity == that.quantity &&
                    Objects.equals(menuItemId, that.menuItemId) &&
                    Objects.equals(name, that.name) &&
                    Objects.equals(price, that.price);
        }

        @Override
        public int hashCode() {
            return Objects.hash(menuItemId, name, price, quantity);
        }
    }

    public enum OrderState {
        PENDING, APPROVED, REJECTED
    }
}