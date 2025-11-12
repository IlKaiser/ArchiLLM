package com.example.logging.api;

import com.example.logging.domain.LogEvent;
import com.example.logging.service.LoggingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/logs")
public class LogEventController {

    private final LoggingService loggingService;

    @Autowired
    public LogEventController(LoggingService loggingService) {
        this.loggingService = loggingService;
    }

    @PostMapping
    public ResponseEntity<Void> submitLogEvent(@RequestBody LogEvent logEvent) {
        loggingService.recordEvent(logEvent);
        return ResponseEntity.accepted().build();
    }

    @GetMapping
    public ResponseEntity<List<LogEvent>> getLogEvents(
            @RequestParam(value = "level", required = false) String level) {
        List<LogEvent> events = loggingService.findEvents(level);
        return ResponseEntity.ok(events);
    }
}