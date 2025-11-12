package com.example.logging.service;

import com.example.logging.event.LogEvent;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

@Service
public class LoggingService {

    // In-memory event store for demonstration. Replace with persistent/event store in production.
    private final List<LogEvent> events = Collections.synchronizedList(new ArrayList<>());

    /**
     * Creates a new log event and stores it.
     *
     * @param message the log message
     * @param level the log level (e.g., INFO, WARN, ERROR)
     * @return the created LogEvent
     */
    public LogEvent createLogEvent(String message, String level) {
        LogEvent event = new LogEvent(
                UUID.randomUUID().toString(),
                message,
                level,
                Instant.now()
        );
        events.add(event);
        // TODO: Publish event to event bus or external system if needed
        return event;
    }

    /**
     * Retrieves all log events.
     *
     * @return list of LogEvent
     */
    public List<LogEvent> getAllLogEvents() {
        return new ArrayList<>(events);
    }

    /**
     * Retrieves log events filtered by level.
     *
     * @param level the log level to filter by
     * @return list of LogEvent with the specified level
     */
    public List<LogEvent> getLogEventsByLevel(String level) {
        List<LogEvent> filtered = new ArrayList<>();
        synchronized (events) {
            for (LogEvent event : events) {
                if (event.getLevel().equalsIgnoreCase(level)) {
                    filtered.add(event);
                }
            }
        }
        return filtered;
    }

    // TODO: Integrate with persistent event store or message broker for production use.
}