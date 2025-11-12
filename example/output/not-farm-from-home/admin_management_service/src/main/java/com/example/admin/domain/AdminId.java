package com.example.admin.domain;

import java.io.Serializable;
import java.util.Objects;

/**
 * Value object representing an admin identifier.
 */
public class AdminId implements Serializable {

    private final String id;

    public AdminId(String id) {
        if (id == null || id.trim().isEmpty()) {
            throw new IllegalArgumentException("AdminId cannot be null or empty");
        }
        this.id = id;
    }

    public String getId() {
        return id;
    }

    // For JPA and serialization frameworks
    protected AdminId() {
        this.id = null;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof AdminId)) return false;
        AdminId adminId = (AdminId) o;
        return Objects.equals(id, adminId.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public String toString() {
        return "AdminId{" +
                "id='" + id + '\'' +
                '}';
    }
}