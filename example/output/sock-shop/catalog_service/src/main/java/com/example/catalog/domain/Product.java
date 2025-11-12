package com.example.catalog.domain;

import java.util.Objects;
import java.util.UUID;
import java.util.List;
import java.util.ArrayList;

/**
 * Aggregate root entity representing a product in the catalog.
 * Implements event sourcing and emits domain events on state changes.
 */
public class Product {

    private final UUID id;
    private String name;
    private String description;
    private double price;

    // Event sourcing: store uncommitted events
    private final transient List<ProductEvent> uncommittedEvents = new ArrayList<>();

    // Constructor for creating a new product
    public Product(UUID id, String name, String description, double price) {
        this.id = Objects.requireNonNull(id);
        this.name = Objects.requireNonNull(name);
        this.description = description;
        this.price = price;
        // Emit ProductCreated event
        applyAndAddEvent(new ProductCreatedEvent(id, name, description, price));
    }

    // Constructor for rehydration from events
    public Product(List<ProductEvent> eventStream) {
        UUID loadedId = null;
        for (ProductEvent event : eventStream) {
            if (event instanceof ProductCreatedEvent) {
                ProductCreatedEvent e = (ProductCreatedEvent) event;
                loadedId = e.getProductId();
                this.name = e.getName();
                this.description = e.getDescription();
                this.price = e.getPrice();
            } else if (event instanceof ProductUpdatedEvent) {
                ProductUpdatedEvent e = (ProductUpdatedEvent) event;
                this.name = e.getName();
                this.description = e.getDescription();
                this.price = e.getPrice();
            }
            // Add more event types as needed
        }
        this.id = loadedId;
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

    // Command method: update product details
    public void update(String name, String description, double price) {
        applyAndAddEvent(new ProductUpdatedEvent(this.id, name, description, price));
    }

    // Event sourcing: apply and record event
    private void applyAndAddEvent(ProductEvent event) {
        apply(event);
        uncommittedEvents.add(event);
    }

    // Apply event to mutate state
    private void apply(ProductEvent event) {
        if (event instanceof ProductCreatedEvent) {
            ProductCreatedEvent e = (ProductCreatedEvent) event;
            this.name = e.getName();
            this.description = e.getDescription();
            this.price = e.getPrice();
        } else if (event instanceof ProductUpdatedEvent) {
            ProductUpdatedEvent e = (ProductUpdatedEvent) event;
            this.name = e.getName();
            this.description = e.getDescription();
            this.price = e.getPrice();
        }
        // Add more event types as needed
    }

    // Return and clear uncommitted events
    public List<ProductEvent> getUncommittedEvents() {
        return new ArrayList<>(uncommittedEvents);
    }

    public void clearUncommittedEvents() {
        uncommittedEvents.clear();
    }

    // Domain event base class
    public static abstract class ProductEvent {
        private final UUID productId;

        protected ProductEvent(UUID productId) {
            this.productId = productId;
        }

        public UUID getProductId() {
            return productId;
        }
    }

    // ProductCreated event
    public static class ProductCreatedEvent extends ProductEvent {
        private final String name;
        private final String description;
        private final double price;

        public ProductCreatedEvent(UUID productId, String name, String description, double price) {
            super(productId);
            this.name = name;
            this.description = description;
            this.price = price;
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
    }

    // ProductUpdated event
    public static class ProductUpdatedEvent extends ProductEvent {
        private final String name;
        private final String description;
        private final double price;

        public ProductUpdatedEvent(UUID productId, String name, String description, double price) {
            super(productId);
            this.name = name;
            this.description = description;
            this.price = price;
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
    }
}