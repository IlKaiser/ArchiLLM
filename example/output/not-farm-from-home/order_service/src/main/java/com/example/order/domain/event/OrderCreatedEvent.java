package com.example.order.domain.event;

import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * Domain event published when a new order is created.
 */
public class OrderCreatedEvent {

    private final Long orderId;
    private final Long consumerId;
    private final Long restaurantId;
    private final List<OrderLineItem> lineItems;
    private final int orderTotal;

    public OrderCreatedEvent(Long orderId, Long consumerId, Long restaurantId, List<OrderLineItem> lineItems, int orderTotal) {
        this.orderId = orderId;
        this.consumerId = consumerId;
        this.restaurantId = restaurantId;
        this.lineItems = lineItems == null ? Collections.emptyList() : Collections.unmodifiableList(lineItems);
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

    public int getOrderTotal() {
        return orderTotal;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof OrderCreatedEvent)) return false;
        OrderCreatedEvent that = (OrderCreatedEvent) o;
        return orderTotal == that.orderTotal &&
                Objects.equals(orderId, that.orderId) &&
                Objects.equals(consumerId, that.consumerId) &&
                Objects.equals(restaurantId, that.restaurantId) &&
                Objects.equals(lineItems, that.lineItems);
    }

    @Override
    public int hashCode() {
        return Objects.hash(orderId, consumerId, restaurantId, lineItems, orderTotal);
    }

    @Override
    public String toString() {
        return "OrderCreatedEvent{" +
                "orderId=" + orderId +
                ", consumerId=" + consumerId +
                ", restaurantId=" + restaurantId +
                ", lineItems=" + lineItems +
                ", orderTotal=" + orderTotal +
                '}';
    }

    // Minimal stub for OrderLineItem (aggregate pattern)
    public static class OrderLineItem {
        private final String menuItemId;
        private final String name;
        private final int price;
        private final int quantity;

        public OrderLineItem(String menuItemId, String name, int price, int quantity) {
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

        public int getPrice() {
            return price;
        }

        public int getQuantity() {
            return quantity;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof OrderLineItem)) return false;
            OrderLineItem that = (OrderLineItem) o;
            return price == that.price &&
                    quantity == that.quantity &&
                    Objects.equals(menuItemId, that.menuItemId) &&
                    Objects.equals(name, that.name);
        }

        @Override
        public int hashCode() {
            return Objects.hash(menuItemId, name, price, quantity);
        }

        @Override
        public String toString() {
            return "OrderLineItem{" +
                    "menuItemId='" + menuItemId + '\'' +
                    ", name='" + name + '\'' +
                    ", price=" + price +
                    ", quantity=" + quantity +
                    '}';
        }
    }
}