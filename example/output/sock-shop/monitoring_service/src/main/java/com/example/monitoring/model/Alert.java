package com.example.monitoring.model;

import javax.persistence.*;

@Entity
public class Alert {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String message;
    private boolean active;

    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }
}