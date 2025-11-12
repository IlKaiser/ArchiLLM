package com.example.authentication.repository;

import com.example.authentication.domain.User;
import java.util.Optional;

// Repository interface for managing User aggregates.
// TODO: Integrate with persistence (e.g., Spring Data JPA, JDBC, etc.)
public interface UserRepository {
    Optional<User> findById(Long id);
    User save(User user);
    // Add more aggregate-specific methods as needed
}