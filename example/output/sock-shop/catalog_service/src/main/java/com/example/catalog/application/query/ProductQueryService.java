package com.example.catalog.application.query;

import com.example.catalog.domain.Product;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

// CQRS Query Service for reading product data (read side)
@Service
public class ProductQueryService {

    // TODO: Inject repository or read model (e.g., JPA, MongoDB, or in-memory projection)
    // Example:
    // private final ProductReadRepository productReadRepository;
    //
    // public ProductQueryService(ProductReadRepository productReadRepository) {
    //     this.productReadRepository = productReadRepository;
    // }

    public List<Product> findAllProducts() {
        // TODO: Implement query logic using read model
        throw new UnsupportedOperationException("Not implemented yet");
    }

    public Optional<Product> findProductById(Long productId) {
        // TODO: Implement query logic using read model
        throw new UnsupportedOperationException("Not implemented yet");
    }
}