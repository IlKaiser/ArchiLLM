package com.example.rating.application.query;

import java.util.Objects;

/**
 * Query object for retrieving a rating by its id.
 * Used in CQRS read model.
 */
public class GetRatingQuery {

    private final Long ratingId;

    public GetRatingQuery(Long ratingId) {
        this.ratingId = ratingId;
    }

    public Long getRatingId() {
        return ratingId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof GetRatingQuery)) return false;
        GetRatingQuery that = (GetRatingQuery) o;
        return Objects.equals(ratingId, that.ratingId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(ratingId);
    }

    @Override
    public String toString() {
        return "GetRatingQuery{" +
                "ratingId=" + ratingId +
                '}';
    }
}