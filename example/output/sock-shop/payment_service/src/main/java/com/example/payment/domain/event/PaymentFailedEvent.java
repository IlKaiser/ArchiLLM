package com.example.payment.domain.event;

import java.time.Instant;
import java.util.Objects;

public class PaymentFailedEvent {

    private final String paymentId;
    private final String orderId;
    private final String reason;
    private final Instant failedAt;

    public PaymentFailedEvent(String paymentId, String orderId, String reason, Instant failedAt) {
        this.paymentId = paymentId;
        this.orderId = orderId;
        this.reason = reason;
        this.failedAt = failedAt;
    }

    public String getPaymentId() {
        return paymentId;
    }

    public String getOrderId() {
        return orderId;
    }

    public String getReason() {
        return reason;
    }

    public Instant getFailedAt() {
        return failedAt;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof PaymentFailedEvent)) return false;
        PaymentFailedEvent that = (PaymentFailedEvent) o;
        return Objects.equals(paymentId, that.paymentId) &&
                Objects.equals(orderId, that.orderId) &&
                Objects.equals(reason, that.reason) &&
                Objects.equals(failedAt, that.failedAt);
    }

    @Override
    public int hashCode() {
        return Objects.hash(paymentId, orderId, reason, failedAt);
    }

    @Override
    public String toString() {
        return "PaymentFailedEvent{" +
                "paymentId='" + paymentId + '\'' +
                ", orderId='" + orderId + '\'' +
                ", reason='" + reason + '\'' +
                ", failedAt=" + failedAt +
                '}';
    }
}