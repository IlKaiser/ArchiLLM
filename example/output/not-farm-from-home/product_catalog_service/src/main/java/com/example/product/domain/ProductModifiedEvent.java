package com.example.product.domain;

import java.time.Instant;

public class ProductModifiedEvent {

    private final Long productId;
    private final String name;
    private final String description;
    private final Double price;
    private final Instant modifiedAt;

    public ProductModifiedEvent(Long productId, String name, String description, Double price, Instant modifiedAt) {
        this.productId = productId;
        this.name = name;
        this.description = description;
        this.price = price;
        this.modifiedAt = modifiedAt;
    }

    public Long getProductId() {
        return productId;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public Double getPrice() {
        return price;
    }

    public Instant getModifiedAt() {
        return modifiedAt;
    }

    @Override
    public String toString() {
        return "ProductModifiedEvent{" +
                "productId=" + productId +
                ", name='" + name + '\'' +
                ", description='" + description + '\'' +
                ", price=" + price +
                ", modifiedAt=" + modifiedAt +
                '}';
    }
}