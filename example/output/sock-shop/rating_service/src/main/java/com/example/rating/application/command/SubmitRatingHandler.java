package com.example.rating.application.command;

import com.example.rating.domain.Rating;
import com.example.rating.domain.RatingRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SubmitRatingHandler {

    private final RatingRepository ratingRepository;

    public SubmitRatingHandler(RatingRepository ratingRepository) {
        this.ratingRepository = ratingRepository;
    }

    @Transactional
    public void handle(SubmitRatingCommand command) {
        // Load or create aggregate
        Rating rating = new Rating(
                command.getOrderId(),
                command.getUserId(),
                command.getScore(),
                command.getComment()
        );
        ratingRepository.save(rating);
        // TODO: Publish events if needed
    }
}