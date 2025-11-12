package com.example.rating.controller;

import com.example.rating.model.Rating;
import com.example.rating.service.RatingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/ratings")
public class RatingController {
    @Autowired
    private RatingService ratingService;

    @PostMapping
    public ResponseEntity<Rating> submitRating(@RequestBody Rating rating) {
        return ResponseEntity.ok(ratingService.submitRating(rating));
    }

    @GetMapping("/{orderId}")
    public ResponseEntity<Rating> getRatingByOrder(@PathVariable Long orderId) {
        return ratingService.getRatingByOrder(orderId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/user/{userId}")
    public List<Rating> getRatingsByUser(@PathVariable String userId) {
        return ratingService.getRatingsByUser(userId);
    }
}