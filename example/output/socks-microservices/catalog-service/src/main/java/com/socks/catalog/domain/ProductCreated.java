package com.socks.catalog.domain;
import com.socks.common.events.DomainEvent;
import java.time.Instant;
public record ProductCreated(String productId, Instant occurredAt) implements DomainEvent {
    @Override public String type(){ return "catalog.product.created"; }
}
