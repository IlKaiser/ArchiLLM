package com.socks.common.events;
import java.time.Instant;
public interface DomainEvent {
    Instant occurredAt();
    String type();
}
