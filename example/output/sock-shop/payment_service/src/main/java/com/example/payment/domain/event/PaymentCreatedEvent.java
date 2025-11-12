package com.example.payment.domain.event;

import java.time.Instant;
import java.util.Objects;

public class PaymentCreatedEvent {

    private final Long paymentId;
    private final Long orderId;
    private final Long amount;
    private final String currency;
    private final Instant createdAt;

    public PaymentCreatedEvent(Long paymentId, Long orderId, Long amount, String currency, Instant createdAt) {
        this.paymentId = paymentId;
        this.orderId = orderId;
        this.amount = amount;
        this.currency = currency;
        this.createdAt = createdAt;
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

    public String getCurrency() {
        return currency;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof PaymentCreatedEvent)) return false;
        PaymentCreatedEvent that = (PaymentCreatedEvent) o;
        return Objects.equals(paymentId, that.paymentId) &&
                Objects.equals(orderId, that.orderId) &&
                Objects.equals(amount, that.amount) &&
                Objects.equals(currency, that.currency) &&
                Objects.equals(createdAt, that.createdAt);
    }

    @Override
    public int hashCode() {
        return Objects.hash(paymentId, orderId, amount, currency, createdAt);
    }

    @Override
    public String toString() {
        return "PaymentCreatedEvent{" +
                "paymentId=" + paymentId +
                ", orderId=" + orderId +
                ", amount=" + amount +
                ", currency='" + currency + '\'' +
                ", createdAt=" + createdAt +
                '}';
    }
}