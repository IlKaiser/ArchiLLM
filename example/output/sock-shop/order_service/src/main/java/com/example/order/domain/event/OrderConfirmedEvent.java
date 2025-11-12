package com.example.order.domain.event;

public class OrderConfirmedEvent {

    private final Long orderId;

    public OrderConfirmedEvent(Long orderId) {
        this.orderId = orderId;
    }

    public Long getOrderId() {
        return orderId;
    }

    @Override
    public String toString() {
        return "OrderConfirmedEvent{" +
                "orderId=" + orderId +
                '}';
    }
}