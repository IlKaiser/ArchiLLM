package com.example.rating.service;

import com.example.rating.model.Rating;
import com.example.rating.repository.RatingRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
public class RatingService {
    @Autowired
    private RatingRepository ratingRepository;

    public Rating submitRating(Rating rating) {
        return ratingRepository.save(rating);
    }

    public Optional<Rating> getRatingByOrder(Long orderId) {
        return ratingRepository.findByOrderId(orderId);
    }

    public List<Rating> getRatingsByUser(String userId) {
        return ratingRepository.findByUserId(userId);
    }
}