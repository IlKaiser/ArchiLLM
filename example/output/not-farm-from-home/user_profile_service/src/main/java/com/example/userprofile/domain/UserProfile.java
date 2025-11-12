package com.example.userprofile.domain;

import java.util.Objects;

/**
 * Aggregate root representing a user profile.
 */
public class UserProfile {

    private Long id;
    private String username;
    private String email;
    private String fullName;

    // TODO: Add more fields as needed

    public UserProfile(Long id, String username, String email, String fullName) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.fullName = fullName;
    }

    public Long getId() {
        return id;
    }

    public String getUsername() {
        return username;
    }

    public String getEmail() {
        return email;
    }

    public String getFullName() {
        return fullName;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public void setFullName(String fullName) {
        this.fullName = fullName;
    }

    // Example business logic method
    public void updateProfile(String email, String fullName) {
        setEmail(email);
        setFullName(fullName);
    }

    // TODO: Add domain logic methods as needed

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof UserProfile)) return false;
        UserProfile that = (UserProfile) o;
        return Objects.equals(id, that.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}