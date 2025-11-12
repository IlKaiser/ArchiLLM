package com.example.rating.domain;

import java.util.Objects;

/**
 * Value object representing the unique identifier of a Rating aggregate.
 */
public class RatingId {

    private final String id;

    public RatingId(String id) {
        if (id == null || id.isEmpty()) {
            throw new IllegalArgumentException("RatingId must not be null or empty");
        }
        this.id = id;
    }

    public String getId() {
        return id;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof RatingId)) return false;
        RatingId ratingId = (RatingId) o;
        return Objects.equals(id, ratingId.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public String toString() {
        return "RatingId{" +
                "id='" + id + '\'' +
                '}';
    }
}