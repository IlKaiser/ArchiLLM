package com.example.admin.domain;

import org.springframework.data.repository.CrudRepository;

// Repository interface for persisting AdminAggregate
public interface AdminRepository extends CrudRepository<AdminAggregate, Long> {
    // Additional query methods can be defined here if needed
}