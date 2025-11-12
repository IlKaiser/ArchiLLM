package com.example.authentication.service;

import com.example.authentication.domain.User;
import com.example.authentication.domain.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class AuthenticationService {

    private final UserRepository userRepository;

    // Simple in-memory session store for demonstration
    private final ConcurrentHashMap<String, String> sessions = new ConcurrentHashMap<>();

    @Autowired
    public AuthenticationService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public User register(String username, String password) {
        // TODO: Add validation, password hashing, etc.
        if (userRepository.findByUsername(username).isPresent()) {
            throw new IllegalArgumentException("Username already exists");
        }
        User user = new User(username, password);
        return userRepository.save(user);
    }

    public String login(String username, String password) {
        Optional<User> userOpt = userRepository.findByUsername(username);
        if (userOpt.isEmpty() || !userOpt.get().getPassword().equals(password)) {
            throw new IllegalArgumentException("Invalid credentials");
        }
        String sessionId = UUID.randomUUID().toString();
        sessions.put(sessionId, userOpt.get().getId());
        return sessionId;
    }

    public void logout(String sessionId) {
        sessions.remove(sessionId);
    }

    public Optional<User> getSessionUser(String sessionId) {
        String userId = sessions.get(sessionId);
        if (userId == null) {
            return Optional.empty();
        }
        return userRepository.findById(userId);
    }

    // TODO: Integrate with external session store or authentication provider if needed
}