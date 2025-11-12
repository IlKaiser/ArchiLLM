package com.example.rating.repository;

import com.example.rating.model.Rating;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface RatingRepository extends JpaRepository<Rating, Long> {
    Optional<Rating> findByOrderId(Long orderId);
    List<Rating> findByUserId(String userId);
}