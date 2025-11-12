package com.example.rating.application.command;

import java.util.Objects;

public class SubmitRatingCommand {

    private final Long targetId;
    private final Long userId;
    private final int score;
    private final String comment;

    public SubmitRatingCommand(Long targetId, Long userId, int score, String comment) {
        this.targetId = targetId;
        this.userId = userId;
        this.score = score;
        this.comment = comment;
    }

    public Long getTargetId() {
        return targetId;
    }

    public Long getUserId() {
        return userId;
    }

    public int getScore() {
        return score;
    }

    public String getComment() {
        return comment;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof SubmitRatingCommand)) return false;
        SubmitRatingCommand that = (SubmitRatingCommand) o;
        return score == that.score &&
                Objects.equals(targetId, that.targetId) &&
                Objects.equals(userId, that.userId) &&
                Objects.equals(comment, that.comment);
    }

    @Override
    public int hashCode() {
        return Objects.hash(targetId, userId, score, comment);
    }

    @Override
    public String toString() {
        return "SubmitRatingCommand{" +
                "targetId=" + targetId +
                ", userId=" + userId +
                ", score=" + score +
                ", comment='" + comment + '\'' +
                '}';
    }
}