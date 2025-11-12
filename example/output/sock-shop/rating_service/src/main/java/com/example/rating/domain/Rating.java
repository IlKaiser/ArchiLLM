package com.example.rating.domain;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Version;
import java.util.Objects;

/**
 * Aggregate root representing a customer rating.
 */
@Entity
public class Rating {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long customerId;
    private Long targetId; // e.g., restaurantId, orderId, etc.
    private int score;
    private String comment;

    @Version
    private Long version;

    protected Rating() {
        // for JPA
    }

    public Rating(Long customerId, Long targetId, int score, String comment) {
        this.customerId = customerId;
        this.targetId = targetId;
        this.score = score;
        this.comment = comment;
    }

    public Long getId() {
        return id;
    }

    public Long getCustomerId() {
        return customerId;
    }

    public Long getTargetId() {
        return targetId;
    }

    public int getScore() {
        return score;
    }

    public String getComment() {
        return comment;
    }

    public Long getVersion() {
        return version;
    }

    public void updateScore(int newScore, String newComment) {
        this.score = newScore;
        this.comment = newComment;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Rating)) return false;
        Rating rating = (Rating) o;
        return Objects.equals(id, rating.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}