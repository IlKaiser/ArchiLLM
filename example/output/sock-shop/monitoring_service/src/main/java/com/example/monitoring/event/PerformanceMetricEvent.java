package com.example.monitoring.event;

import java.time.Instant;

public class PerformanceMetricEvent {

    private String serviceName;
    private String metricName;
    private double value;
    private Instant timestamp;

    public PerformanceMetricEvent() {
    }

    public PerformanceMetricEvent(String serviceName, String metricName, double value, Instant timestamp) {
        this.serviceName = serviceName;
        this.metricName = metricName;
        this.value = value;
        this.timestamp = timestamp;
    }

    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }

    public String getMetricName() {
        return metricName;
    }

    public void setMetricName(String metricName) {
        this.metricName = metricName;
    }

    public double getValue() {
        return value;
    }

    public void setValue(double value) {
        this.value = value;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public String toString() {
        return "PerformanceMetricEvent{" +
                "serviceName='" + serviceName + '\'' +
                ", metricName='" + metricName + '\'' +
                ", value=" + value +
                ", timestamp=" + timestamp +
                '}';
    }
}