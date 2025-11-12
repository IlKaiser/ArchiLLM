package com.example.logging.service;

import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

@Service
public class LogEventStore {

    private final List<LogEvent> events = new ArrayList<>();

    public void appendEvent(String message, String level) {
        LogEvent event = new LogEvent(UUID.randomUUID().toString(), Instant.now(), message, level);
        // TODO: Persist event to durable storage
        synchronized (events) {
            events.add(event);
        }
    }

    public List<LogEvent> getAllEvents() {
        // TODO: Retrieve events from persistent storage
        synchronized (events) {
            return Collections.unmodifiableList(new ArrayList<>(events));
        }
    }

    public static class LogEvent {
        private final String id;
        private final Instant timestamp;
        private final String message;
        private final String level;

        public LogEvent(String id, Instant timestamp, String message, String level) {
            this.id = id;
            this.timestamp = timestamp;
            this.message = message;
            this.level = level;
        }

        public String getId() {
            return id;
        }

        public Instant getTimestamp() {
            return timestamp;
        }

        public String getMessage() {
            return message;
        }

        public String getLevel() {
            return level;
        }
    }
}