package com.example.product.domain;

import java.io.Serializable;
import java.util.Objects;

/**
 * Value object representing the identity of a Product aggregate.
 */
public class ProductId implements Serializable {

    private final String id;

    public ProductId(String id) {
        if (id == null || id.isEmpty()) {
            throw new IllegalArgumentException("ProductId must not be null or empty");
        }
        this.id = id;
    }

    public String getId() {
        return id;
    }

    // For JPA and serialization frameworks
    protected ProductId() {
        this.id = null;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof ProductId)) return false;
        ProductId productId = (ProductId) o;
        return Objects.equals(id, productId.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public String toString() {
        return "ProductId{" +
                "id='" + id + '\'' +
                '}';
    }
}