package com.example.payment.domain;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

public class Payment {

    public enum Status {
        PENDING,
        COMPLETED,
        FAILED
    }

    private final String id;
    private final String orderId;
    private final double amount;
    private final LocalDateTime createdAt;
    private Status status;

    // Domain events
    private final List<PaymentEvent> domainEvents = new ArrayList<>();

    public Payment(String orderId, double amount) {
        this.id = UUID.randomUUID().toString();
        this.orderId = orderId;
        this.amount = amount;
        this.createdAt = LocalDateTime.now();
        this.status = Status.PENDING;
        domainEvents.add(new PaymentCreatedEvent(this.id, this.orderId, this.amount, this.createdAt));
    }

    // For ORM/serialization
    protected Payment() {
        this.id = null;
        this.orderId = null;
        this.amount = 0;
        this.createdAt = null;
        this.status = null;
    }

    public void complete() {
        if (status != Status.PENDING) {
            throw new IllegalStateException("Payment is not in a pending state");
        }
        this.status = Status.COMPLETED;
        domainEvents.add(new PaymentCompletedEvent(this.id, LocalDateTime.now()));
    }

    public void fail(String reason) {
        if (status != Status.PENDING) {
            throw new IllegalStateException("Payment is not in a pending state");
        }
        this.status = Status.FAILED;
        domainEvents.add(new PaymentFailedEvent(this.id, LocalDateTime.now(), reason));
    }

    public String getId() {
        return id;
    }

    public String getOrderId() {
        return orderId;
    }

    public double getAmount() {
        return amount;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public Status getStatus() {
        return status;
    }

    public List<PaymentEvent> getDomainEvents() {
        return Collections.unmodifiableList(domainEvents);
    }

    public void clearDomainEvents() {
        domainEvents.clear();
    }

    // --- Domain Events ---

    public interface PaymentEvent {}

    public static class PaymentCreatedEvent implements PaymentEvent {
        private final String paymentId;
        private final String orderId;
        private final double amount;
        private final LocalDateTime createdAt;

        public PaymentCreatedEvent(String paymentId, String orderId, double amount, LocalDateTime createdAt) {
            this.paymentId = paymentId;
            this.orderId = orderId;
            this.amount = amount;
            this.createdAt = createdAt;
        }

        public String getPaymentId() {
            return paymentId;
        }

        public String getOrderId() {
            return orderId;
        }

        public double getAmount() {
            return amount;
        }

        public LocalDateTime getCreatedAt() {
            return createdAt;
        }
    }

    public static class PaymentCompletedEvent implements PaymentEvent {
        private final String paymentId;
        private final LocalDateTime completedAt;

        public PaymentCompletedEvent(String paymentId, LocalDateTime completedAt) {
            this.paymentId = paymentId;
            this.completedAt = completedAt;
        }

        public String getPaymentId() {
            return paymentId;
        }

        public LocalDateTime getCompletedAt() {
            return completedAt;
        }
    }

    public static class PaymentFailedEvent implements PaymentEvent {
        private final String paymentId;
        private final LocalDateTime failedAt;
        private final String reason;

        public PaymentFailedEvent(String paymentId, LocalDateTime failedAt, String reason) {
            this.paymentId = paymentId;
            this.failedAt = failedAt;
            this.reason = reason;
        }

        public String getPaymentId() {
            return paymentId;
        }

        public LocalDateTime getFailedAt() {
            return failedAt;
        }

        public String getReason() {
            return reason;
        }
    }
}