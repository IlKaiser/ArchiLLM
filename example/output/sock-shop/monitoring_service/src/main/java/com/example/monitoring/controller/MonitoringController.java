package com.example.monitoring.controller;

import com.example.monitoring.model.Alert;
import com.example.monitoring.model.Metric;
import com.example.monitoring.service.MonitoringService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
public class MonitoringController {
    @Autowired
    private MonitoringService monitoringService;

    @GetMapping("/metrics")
    public List<Metric> getMetrics() {
        return monitoringService.getMetrics();
    }

    @GetMapping("/alerts")
    public List<Alert> getAlerts() {
        return monitoringService.getAlerts();
    }
}