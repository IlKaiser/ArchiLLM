package com.example.product.domain;

import java.time.Instant;

public abstract class ProductEvent {

    private final Instant occurredAt;

    protected ProductEvent() {
        this.occurredAt = Instant.now();
    }

    protected ProductEvent(Instant occurredAt) {
        this.occurredAt = occurredAt;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }
}