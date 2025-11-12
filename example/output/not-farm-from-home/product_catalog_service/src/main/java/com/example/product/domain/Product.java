package com.example.product.domain;

import java.util.Objects;
import java.util.UUID;
import org.springframework.data.annotation.Id;
import org.springframework.data.domain.AbstractAggregateRoot;

// Domain event base class
public abstract class ProductEvent {
    private final UUID productId;

    public ProductEvent(UUID productId) {
        this.productId = productId;
    }

    public UUID getProductId() {
        return productId;
    }
}

// Example event: ProductCreated
class ProductCreatedEvent extends ProductEvent {
    private final String name;
    private final String description;
    private final double price;

    public ProductCreatedEvent(UUID productId, String name, String description, double price) {
        super(productId);
        this.name = name;
        this.description = description;
        this.price = price;
    }

    public String getName() { return name; }
    public String getDescription() { return description; }
    public double getPrice() { return price; }
}

// Aggregate root
public class Product extends AbstractAggregateRoot<Product> {

    @Id
    private UUID id;
    private String name;
    private String description;
    private double price;

    protected Product() {
        // for JPA or serialization
    }

    public Product(String name, String description, double price) {
        this.id = UUID.randomUUID();
        this.name = name;
        this.description = description;
        this.price = price;
        registerEvent(new ProductCreatedEvent(this.id, name, description, price));
    }

    public UUID getId() {
        return id;
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

    public void changePrice(double newPrice) {
        if (this.price != newPrice) {
            this.price = newPrice;
            // TODO: register ProductPriceChangedEvent
        }
    }

    // TODO: Add more domain logic and events as needed

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Product)) return false;
        Product product = (Product) o;
        return Objects.equals(id, product.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}