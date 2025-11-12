package com.example.logging.domain.event;

import java.time.Instant;
import java.util.Objects;

/**
 * Domain event representing a log entry received or created.
 */
public class LogEvent {

    private final String logId;
    private final String message;
    private final String level;
    private final Instant timestamp;

    // TODO: Add additional fields as needed (e.g., source, context, etc.)

    public LogEvent(String logId, String message, String level, Instant timestamp) {
        this.logId = logId;
        this.message = message;
        this.level = level;
        this.timestamp = timestamp;
    }

    public String getLogId() {
        return logId;
    }

    public String getMessage() {
        return message;
    }

    public String getLevel() {
        return level;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof LogEvent)) return false;
        LogEvent logEvent = (LogEvent) o;
        return Objects.equals(logId, logEvent.logId) &&
                Objects.equals(message, logEvent.message) &&
                Objects.equals(level, logEvent.level) &&
                Objects.equals(timestamp, logEvent.timestamp);
    }

    @Override
    public int hashCode() {
        return Objects.hash(logId, message, level, timestamp);
    }

    @Override
    public String toString() {
        return "LogEvent{" +
                "logId='" + logId + '\'' +
                ", message='" + message + '\'' +
                ", level='" + level + '\'' +
                ", timestamp=" + timestamp +
                '}';
    }
}