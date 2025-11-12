package com.example.rating.api;

import com.example.rating.application.RatingService;
import com.example.rating.domain.Rating;
import com.example.rating.application.SubmitRatingCommand;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/ratings")
public class RatingCommandController {

    private final RatingService ratingService;

    public RatingCommandController(RatingService ratingService) {
        this.ratingService = ratingService;
    }

    @PostMapping
    public ResponseEntity<Rating> submitRating(@RequestBody SubmitRatingCommand command) {
        Rating rating = ratingService.submitRating(command);
        return new ResponseEntity<>(rating, HttpStatus.CREATED);
    }
}