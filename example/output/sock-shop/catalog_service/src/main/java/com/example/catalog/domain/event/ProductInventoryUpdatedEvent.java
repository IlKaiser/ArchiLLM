package com.example.catalog.domain.event;

import java.time.Instant;
import java.util.Objects;

public class ProductInventoryUpdatedEvent {

    private final Long productId;
    private final int oldQuantity;
    private final int newQuantity;
    private final Instant occurredAt;

    public ProductInventoryUpdatedEvent(Long productId, int oldQuantity, int newQuantity, Instant occurredAt) {
        this.productId = productId;
        this.oldQuantity = oldQuantity;
        this.newQuantity = newQuantity;
        this.occurredAt = occurredAt;
    }

    public Long getProductId() {
        return productId;
    }

    public int getOldQuantity() {
        return oldQuantity;
    }

    public int getNewQuantity() {
        return newQuantity;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof ProductInventoryUpdatedEvent)) return false;
        ProductInventoryUpdatedEvent that = (ProductInventoryUpdatedEvent) o;
        return oldQuantity == that.oldQuantity &&
                newQuantity == that.newQuantity &&
                Objects.equals(productId, that.productId) &&
                Objects.equals(occurredAt, that.occurredAt);
    }

    @Override
    public int hashCode() {
        return Objects.hash(productId, oldQuantity, newQuantity, occurredAt);
    }

    @Override
    public String toString() {
        return "ProductInventoryUpdatedEvent{" +
                "productId=" + productId +
                ", oldQuantity=" + oldQuantity +
                ", newQuantity=" + newQuantity +
                ", occurredAt=" + occurredAt +
                '}';
    }
}