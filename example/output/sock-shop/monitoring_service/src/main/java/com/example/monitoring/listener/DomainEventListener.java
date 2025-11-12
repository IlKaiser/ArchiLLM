package com.example.monitoring.listener;

import com.example.monitoring.service.MonitoringService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

// TODO: Replace Object with actual domain event types as needed
@Component
public class DomainEventListener {

    private final MonitoringService monitoringService;

    @Autowired
    public DomainEventListener(MonitoringService monitoringService) {
        this.monitoringService = monitoringService;
    }

    @EventListener
    public void handleDomainEvent(Object event) {
        // TODO: Add filtering/handling for specific domain event types
        monitoringService.processEvent(event);
    }
}