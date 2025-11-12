package com.example.catalog.application.event;

import com.example.catalog.domain.event.ProductEvent;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Component;

@Component
public class ProductEventPublisher {

    private final ApplicationEventPublisher applicationEventPublisher;

    public ProductEventPublisher(ApplicationEventPublisher applicationEventPublisher) {
        this.applicationEventPublisher = applicationEventPublisher;
    }

    public void publish(ProductEvent event) {
        // TODO: Integrate with external messaging/event bus
        applicationEventPublisher.publishEvent(event);
    }
}