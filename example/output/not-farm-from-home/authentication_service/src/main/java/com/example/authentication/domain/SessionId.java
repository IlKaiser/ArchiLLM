package com.example.authentication.domain;

import java.util.Objects;

/**
 * Value object representing a session identity.
 */
public class SessionId {

    private final String id;

    public SessionId(String id) {
        if (id == null || id.isEmpty()) {
            throw new IllegalArgumentException("SessionId cannot be null or empty");
        }
        this.id = id;
    }

    public String getId() {
        return id;
    }

    // Value object equality
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof SessionId)) return false;
        SessionId sessionId = (SessionId) o;
        return Objects.equals(id, sessionId.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public String toString() {
        return "SessionId{" +
                "id='" + id + '\'' +
                '}';
    }
}