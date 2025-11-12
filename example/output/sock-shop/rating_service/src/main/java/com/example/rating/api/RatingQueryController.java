package com.example.rating.api;

import com.example.rating.query.RatingQueryService;
import com.example.rating.query.RatingView;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class RatingQueryController {

    private final RatingQueryService ratingQueryService;

    public RatingQueryController(RatingQueryService ratingQueryService) {
        this.ratingQueryService = ratingQueryService;
    }

    @GetMapping("/ratings/{entityId}")
    public List<RatingView> getRatingsByEntity(@PathVariable Long entityId) {
        return ratingQueryService.findRatingsByEntityId(entityId);
    }

    @GetMapping("/ratings/{entityId}/average")
    public Double getAverageRating(@PathVariable Long entityId) {
        return ratingQueryService.findAverageRatingByEntityId(entityId);
    }
}