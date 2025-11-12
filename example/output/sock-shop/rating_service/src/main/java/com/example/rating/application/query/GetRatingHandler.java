package com.example.rating.application.query;

import com.example.rating.domain.Rating;
import com.example.rating.domain.RatingRepository;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class GetRatingHandler {

    private final RatingRepository ratingRepository;

    public GetRatingHandler(RatingRepository ratingRepository) {
        this.ratingRepository = ratingRepository;
    }

    public Optional<Rating> handle(GetRatingQuery query) {
        // CQRS Query handler: fetch Rating aggregate by id
        return ratingRepository.findById(query.getRatingId());
    }
}