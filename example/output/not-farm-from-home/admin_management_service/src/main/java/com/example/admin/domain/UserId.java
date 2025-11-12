package com.example.admin.domain;

import java.io.Serializable;
import java.util.Objects;

/**
 * Value object representing a user identifier.
 */
public class UserId implements Serializable {

    private final String id;

    public UserId(String id) {
        if (id == null || id.isEmpty()) {
            throw new IllegalArgumentException("UserId cannot be null or empty");
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
        if (!(o instanceof UserId)) return false;
        UserId userId = (UserId) o;
        return Objects.equals(id, userId.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public String toString() {
        return "UserId{" +
                "id='" + id + '\'' +
                '}';
    }
}