package com.socks.logging.domain;
import java.time.Instant;
public record LogEntry(String id, String eventType, String eventData, Instant timestamp) {}
