package com.example.admin.domain.event;

import java.time.Instant;
import java.util.Objects;

public class UserDeletedEvent {

    private final Long userId;
    private final Instant deletedAt;

    public UserDeletedEvent(Long userId, Instant deletedAt) {
        this.userId = userId;
        this.deletedAt = deletedAt;
    }

    public Long getUserId() {
        return userId;
    }

    public Instant getDeletedAt() {
        return deletedAt;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof UserDeletedEvent)) return false;
        UserDeletedEvent that = (UserDeletedEvent) o;
        return Objects.equals(userId, that.userId) &&
                Objects.equals(deletedAt, that.deletedAt);
    }

    @Override
    public int hashCode() {
        return Objects.hash(userId, deletedAt);
    }

    @Override
    public String toString() {
        return "UserDeletedEvent{" +
                "userId=" + userId +
                ", deletedAt=" + deletedAt +
                '}';
    }
}