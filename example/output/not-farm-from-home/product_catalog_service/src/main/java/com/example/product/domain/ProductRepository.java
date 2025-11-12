package com.example.product.domain;

import org.springframework.data.repository.CrudRepository;

// Repository interface for managing Product aggregates
public interface ProductRepository extends CrudRepository<Product, Long> {
    // TODO: Add custom query methods if needed
}