package com.example.rating.domain;

import org.springframework.data.repository.CrudRepository;

// Repository interface for persisting Rating aggregates.
public interface RatingRepository extends CrudRepository<Rating, Long> {
    // TODO: Add custom query methods if needed for CQRS read models.
}