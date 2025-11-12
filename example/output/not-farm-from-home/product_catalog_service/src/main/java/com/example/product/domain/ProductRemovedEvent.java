package com.example.product.domain;

import java.time.Instant;

public class ProductRemovedEvent {

    private final String productId;
    private final Instant removedAt;

    public ProductRemovedEvent(String productId, Instant removedAt) {
        this.productId = productId;
        this.removedAt = removedAt;
    }

    public String getProductId() {
        return productId;
    }

    public Instant getRemovedAt() {
        return removedAt;
    }

    @Override
    public String toString() {
        return "ProductRemovedEvent{" +
                "productId='" + productId + '\'' +
                ", removedAt=" + removedAt +
                '}';
    }
}