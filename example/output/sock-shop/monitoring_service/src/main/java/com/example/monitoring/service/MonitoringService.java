package com.example.monitoring.service;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.monitoring.events.MonitoringEvent;

@Service
public class MonitoringService {

    private final ApplicationEventPublisher eventPublisher;

    @Autowired
    public MonitoringService(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }

    public void monitor(String resource, String status) {
        // Core monitoring logic goes here
        // TODO: Add integration with metrics/logging systems

        // Publish a domain event
        MonitoringEvent event = new MonitoringEvent(this, resource, status);
        eventPublisher.publishEvent(event);
    }
}