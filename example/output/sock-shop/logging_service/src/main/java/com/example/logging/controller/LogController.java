package com.example.logging.controller;

import com.example.logging.model.LogEvent;
import com.example.logging.service.LogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/logs")
public class LogController {
    @Autowired
    private LogService logService;

    @PostMapping
    public ResponseEntity<LogEvent> recordLog(@RequestBody LogEvent logEvent) {
        return ResponseEntity.ok(logService.recordLog(logEvent));
    }

    @GetMapping
    public List<LogEvent> getLogs(@RequestParam(required = false) String filter,
                                  @RequestParam(required = false) String dateRange,
                                  @RequestParam(required = false) String service) {
        return logService.getLogs(filter, dateRange, service);
    }
}