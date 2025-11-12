package com.example.admin.domain;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

// Aggregate root representing administrator and admin actions.
public class AdminAggregate {

    private Long id;
    private String username;
    private String email;
    private boolean active;

    // Domain events raised by this aggregate
    private final List<Object> domainEvents = new ArrayList<>();

    protected AdminAggregate() {
        // for ORM
    }

    public AdminAggregate(Long id, String username, String email) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.active = true;
        AdminCreatedEvent event = new AdminCreatedEvent(id, username, email);
        domainEvents.add(event);
    }

    public void deactivate() {
        if (!active) return;
        this.active = false;
        AdminDeactivatedEvent event = new AdminDeactivatedEvent(id);
        domainEvents.add(event);
    }

    public void changeEmail(String newEmail) {
        if (Objects.equals(this.email, newEmail)) return;
        this.email = newEmail;
        AdminEmailChangedEvent event = new AdminEmailChangedEvent(id, newEmail);
        domainEvents.add(event);
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

    public boolean isActive() {
        return active;
    }

    public List<Object> getDomainEvents() {
        return Collections.unmodifiableList(domainEvents);
    }

    public void clearDomainEvents() {
        domainEvents.clear();
    }

    // --- Domain Events ---

    public static class AdminCreatedEvent {
        private final Long id;
        private final String username;
        private final String email;

        public AdminCreatedEvent(Long id, String username, String email) {
            this.id = id;
            this.username = username;
            this.email = email;
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
    }

    public static class AdminDeactivatedEvent {
        private final Long id;

        public AdminDeactivatedEvent(Long id) {
            this.id = id;
        }

        public Long getId() {
            return id;
        }
    }

    public static class AdminEmailChangedEvent {
        private final Long id;
        private final String newEmail;

        public AdminEmailChangedEvent(Long id, String newEmail) {
            this.id = id;
            this.newEmail = newEmail;
        }

        public Long getId() {
            return id;
        }

        public String getNewEmail() {
            return newEmail;
        }
    }
}