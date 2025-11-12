package com.example.cart.domain;

import org.springframework.data.repository.CrudRepository;

// Repository interface for Cart aggregate persistence
public interface CartRepository extends CrudRepository<Cart, Long> {
    // TODO: Add custom query methods if needed for CQRS read models
}