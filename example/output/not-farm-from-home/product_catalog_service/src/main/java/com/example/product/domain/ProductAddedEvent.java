package com.example.product.domain;

import java.util.Objects;

public class ProductAddedEvent {

    private final String productId;
    private final String name;
    private final String description;
    private final double price;

    public ProductAddedEvent(String productId, String name, String description, double price) {
        this.productId = productId;
        this.name = name;
        this.description = description;
        this.price = price;
    }

    public String getProductId() {
        return productId;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public double getPrice() {
        return price;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof ProductAddedEvent)) return false;
        ProductAddedEvent that = (ProductAddedEvent) o;
        return Double.compare(that.price, price) == 0 &&
                Objects.equals(productId, that.productId) &&
                Objects.equals(name, that.name) &&
                Objects.equals(description, that.description);
    }

    @Override
    public int hashCode() {
        return Objects.hash(productId, name, description, price);
    }

    @Override
    public String toString() {
        return "ProductAddedEvent{" +
                "productId='" + productId + '\'' +
                ", name='" + name + '\'' +
                ", description='" + description + '\'' +
                ", price=" + price +
                '}';
    }
}