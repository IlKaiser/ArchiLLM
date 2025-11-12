package com.example.authentication.repository;

import com.example.authentication.domain.Session;
import java.util.Optional;
import java.util.List;

// TODO: Integrate with persistence (e.g., Spring Data JPA, JDBC, etc.)
public interface SessionRepository {

    Optional<Session> findById(String sessionId);

    void save(Session session);

    void deleteById(String sessionId);

    List<Session> findByUserId(String userId);

}