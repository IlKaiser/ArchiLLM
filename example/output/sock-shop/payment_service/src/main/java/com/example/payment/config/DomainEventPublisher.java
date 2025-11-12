package com.example.payment.config;

import org.springframework.stereotype.Component;
import com.example.payment.domain.event.DomainEvent;

@Component
public class DomainEventPublisher {

    // TODO: Integrate with messaging/event bus (e.g., Kafka, Eventuate, etc.)

    public void publish(String aggregateType, String aggregateId, DomainEvent event) {
        // TODO: Implement event publishing logic
        // For now, just log or stub
        System.out.printf("Publishing event: type=%s, id=%s, event=%s%n", aggregateType, aggregateId, event);
    }
}