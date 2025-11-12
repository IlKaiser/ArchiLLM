package com.example.authentication.domain;

import java.util.Objects;

/**
 * Value object representing a user's identity.
 */
public class UserId {

    private final String id;

    public UserId(String id) {
        // TODO: Add validation logic if needed
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