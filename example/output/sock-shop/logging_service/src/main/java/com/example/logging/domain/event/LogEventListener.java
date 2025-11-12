package com.example.logging.domain.event;

import org.springframework.stereotype.Component;
import org.springframework.context.event.EventListener;

// TODO: Integrate with messaging/event bus (e.g., Kafka, RabbitMQ, etc.)

@Component
public class LogEventListener {

    @EventListener
    public void handleLogEvent(LogEvent event) {
        // TODO: Implement event handling logic
        System.out.println("Received LogEvent: " + event);
    }
}