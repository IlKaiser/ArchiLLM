package com.example.catalog.domain;

import java.util.Optional;
import java.util.List;

/**
 * Repository interface for managing Product aggregates.
 * 
 * Note: This is a domain-driven design aggregate repository.
 * Persistence and event publishing should be implemented in the infrastructure layer.
 */
public interface ProductRepository {

    Product save(Product product);

    Optional<Product> findById(Long id);

    List<Product> findAll();

    void deleteById(Long id);

    // TODO: Integrate with event publishing mechanism for domain events

    // TODO: Implement persistence (e.g., JPA, JDBC, etc.) in infrastructure layer

}