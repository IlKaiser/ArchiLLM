package com.example.admin.domain.event;

import com.example.admin.domain.event.events.AdminDomainEvent;
import org.springframework.stereotype.Component;

@Component
public class AdminEventPublisher {

    public void publish(AdminDomainEvent event) {
        // TODO: Integrate with event bus or messaging system to publish domain events
    }
}