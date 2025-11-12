package com.example.order.domain.event;

public class OrderCancelledEvent {

    private final Long orderId;
    private final String reason;

    public OrderCancelledEvent(Long orderId, String reason) {
        this.orderId = orderId;
        this.reason = reason;
    }

    public Long getOrderId() {
        return orderId;
    }

    public String getReason() {
        return reason;
    }

    @Override
    public String toString() {
        return "OrderCancelledEvent{" +
                "orderId=" + orderId +
                ", reason='" + reason + '\'' +
                '}';
    }
}