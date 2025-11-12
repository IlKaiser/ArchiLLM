package com.example.payment.domain.event;

import java.time.Instant;
import java.util.Objects;

public class PaymentCompletedEvent {

    private final Long paymentId;
    private final Long orderId;
    private final Long amount;
    private final Instant completedAt;

    public PaymentCompletedEvent(Long paymentId, Long orderId, Long amount, Instant completedAt) {
        this.paymentId = paymentId;
        this.orderId = orderId;
        this.amount = amount;
        this.completedAt = completedAt;
    }

    public Long getPaymentId() {
        return paymentId;
    }

    public Long getOrderId() {
        return orderId;
    }

    public Long getAmount() {
        return amount;
    }

    public Instant getCompletedAt() {
        return completedAt;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof PaymentCompletedEvent)) return false;
        PaymentCompletedEvent that = (PaymentCompletedEvent) o;
        return Objects.equals(paymentId, that.paymentId) &&
                Objects.equals(orderId, that.orderId) &&
                Objects.equals(amount, that.amount) &&
                Objects.equals(completedAt, that.completedAt);
    }

    @Override
    public int hashCode() {
        return Objects.hash(paymentId, orderId, amount, completedAt);
    }

    @Override
    public String toString() {
        return "PaymentCompletedEvent{" +
                "paymentId=" + paymentId +
                ", orderId=" + orderId +
                ", amount=" + amount +
                ", completedAt=" + completedAt +
                '}';
    }
}