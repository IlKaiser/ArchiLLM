package com.example.product.application;

import com.example.product.domain.Product;
import com.example.product.domain.ProductRepository;
import com.example.product.domain.event.ProductCreatedEvent;
import com.example.product.domain.event.ProductUpdatedEvent;
import com.example.product.domain.event.ProductDeletedEvent;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
public class ProductCatalogService {

    private final ProductRepository productRepository;
    private final ApplicationEventPublisher eventPublisher;

    public ProductCatalogService(ProductRepository productRepository,
                                 ApplicationEventPublisher eventPublisher) {
        this.productRepository = productRepository;
        this.eventPublisher = eventPublisher;
    }

    @Transactional
    public Product createProduct(String name, String description, double price) {
        Product product = new Product(name, description, price);
        productRepository.save(product);
        eventPublisher.publishEvent(new ProductCreatedEvent(product.getId(), name, description, price));
        return product;
    }

    @Transactional
    public Optional<Product> updateProduct(Long productId, String name, String description, double price) {
        Optional<Product> productOpt = productRepository.findById(productId);
        if (productOpt.isPresent()) {
            Product product = productOpt.get();
            product.update(name, description, price);
            productRepository.save(product);
            eventPublisher.publishEvent(new ProductUpdatedEvent(product.getId(), name, description, price));
            return Optional.of(product);
        }
        return Optional.empty();
    }

    @Transactional
    public boolean deleteProduct(Long productId) {
        Optional<Product> productOpt = productRepository.findById(productId);
        if (productOpt.isPresent()) {
            productRepository.deleteById(productId);
            eventPublisher.publishEvent(new ProductDeletedEvent(productId));
            return true;
        }
        return false;
    }

    @Transactional(readOnly = true)
    public Optional<Product> getProduct(Long productId) {
        return productRepository.findById(productId);
    }

    @Transactional(readOnly = true)
    public List<Product> listProducts() {
        return productRepository.findAll();
    }

    // TODO: Integrate with Order saga for product reservation/stock management

    // TODO: Implement API composition for product details with other services

    // TODO: Publish domain events to external event bus if needed
}