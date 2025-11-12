package com.example.admin.domain.event;

import java.time.Instant;

public abstract class AdminEvent {

    private final Instant occurredAt;

    protected AdminEvent() {
        this.occurredAt = Instant.now();
    }

    protected AdminEvent(Instant occurredAt) {
        this.occurredAt = occurredAt;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }
}