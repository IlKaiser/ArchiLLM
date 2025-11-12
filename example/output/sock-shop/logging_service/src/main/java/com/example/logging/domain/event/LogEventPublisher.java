package com.example.logging.domain.event;

import org.springframework.stereotype.Component;

@Component
public class LogEventPublisher {

    // TODO: Inject messaging/event bus integration here

    public void publish(LogEvent event) {
        // TODO: Publish the event to the event bus
        // For now, just log or stub
        System.out.println("Publishing event: " + event);
    }
}