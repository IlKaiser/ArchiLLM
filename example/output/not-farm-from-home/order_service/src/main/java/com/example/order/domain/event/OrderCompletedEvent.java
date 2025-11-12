package com.example.order.domain.event;

public class OrderCompletedEvent {

    private final Long orderId;

    public OrderCompletedEvent(Long orderId) {
        this.orderId = orderId;
    }

    public Long getOrderId() {
        return orderId;
    }

    @Override
    public String toString() {
        return "OrderCompletedEvent{" +
                "orderId=" + orderId +
                '}';
    }
}