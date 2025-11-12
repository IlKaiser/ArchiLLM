package com.example.order.domain.event;

public class OrderCancelledEvent {

    private final Long orderId;

    public OrderCancelledEvent(Long orderId) {
        this.orderId = orderId;
    }

    public Long getOrderId() {
        return orderId;
    }

    @Override
    public String toString() {
        return "OrderCancelledEvent{" +
                "orderId=" + orderId +
                '}';
    }
}