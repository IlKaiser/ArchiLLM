package com.example.monitoring.event;

import java.time.Instant;

public class ServiceHealthChangedEvent {

    private String serviceName;
    private String previousStatus;
    private String currentStatus;
    private Instant timestamp;

    public ServiceHealthChangedEvent() {
    }

    public ServiceHealthChangedEvent(String serviceName, String previousStatus, String currentStatus, Instant timestamp) {
        this.serviceName = serviceName;
        this.previousStatus = previousStatus;
        this.currentStatus = currentStatus;
        this.timestamp = timestamp;
    }

    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }

    public String getPreviousStatus() {
        return previousStatus;
    }

    public void setPreviousStatus(String previousStatus) {
        this.previousStatus = previousStatus;
    }

    public String getCurrentStatus() {
        return currentStatus;
    }

    public void setCurrentStatus(String currentStatus) {
        this.currentStatus = currentStatus;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public String toString() {
        return "ServiceHealthChangedEvent{" +
                "serviceName='" + serviceName + '\'' +
                ", previousStatus='" + previousStatus + '\'' +
                ", currentStatus='" + currentStatus + '\'' +
                ", timestamp=" + timestamp +
                '}';
    }
}