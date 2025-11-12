package com.example.userprofile.domain;

import java.util.Optional;

public interface UserProfileRepository {
    Optional<UserProfile> findById(Long id);
    UserProfile save(UserProfile userProfile);
    // TODO: Add other aggregate-specific methods as needed
}