package com.example.catalog.application.event;

import com.example.catalog.domain.event.ProductCreatedEvent;
import com.example.catalog.domain.event.ProductUpdatedEvent;
import com.example.catalog.domain.event.ProductDeletedEvent;
import org.springframework.stereotype.Component;
import org.springframework.context.event.EventListener;

@Component
public class ProductEventListener {

    // TODO: Integrate with messaging infrastructure (e.g., Kafka, RabbitMQ)

    @EventListener
    public void handleProductCreated(ProductCreatedEvent event) {
        // Handle product created event
        // TODO: Publish event to message broker
    }

    @EventListener
    public void handleProductUpdated(ProductUpdatedEvent event) {
        // Handle product updated event
        // TODO: Publish event to message broker
    }

    @EventListener
    public void handleProductDeleted(ProductDeletedEvent event) {
        // Handle product deleted event
        // TODO: Publish event to message broker
    }
}