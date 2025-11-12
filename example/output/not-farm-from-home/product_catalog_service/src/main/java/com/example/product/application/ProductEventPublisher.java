package com.example.product.application;

import com.example.product.domain.event.ProductDomainEvent;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Component;

@Component
public class ProductEventPublisher {

    private final ApplicationEventPublisher applicationEventPublisher;

    public ProductEventPublisher(ApplicationEventPublisher applicationEventPublisher) {
        this.applicationEventPublisher = applicationEventPublisher;
    }

    public void publish(ProductDomainEvent event) {
        // TODO: Integrate with real event bus or messaging system if needed
        applicationEventPublisher.publishEvent(event);
    }
}