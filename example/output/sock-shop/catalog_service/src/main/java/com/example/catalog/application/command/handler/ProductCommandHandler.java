package com.example.catalog.application.command.handler;

import com.example.catalog.domain.Product;
import com.example.catalog.domain.ProductRepository;
import com.example.catalog.domain.event.ProductCreatedEvent;
import com.example.catalog.domain.event.ProductUpdatedEvent;
import com.example.catalog.application.command.CreateProductCommand;
import com.example.catalog.application.command.UpdateProductCommand;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProductCommandHandler {

    private final ProductRepository productRepository;
    private final ApplicationEventPublisher eventPublisher;

    public ProductCommandHandler(ProductRepository productRepository, ApplicationEventPublisher eventPublisher) {
        this.productRepository = productRepository;
        this.eventPublisher = eventPublisher;
    }

    @Transactional
    public Product handle(CreateProductCommand command) {
        Product product = new Product(command.getName(), command.getDescription(), command.getPrice());
        productRepository.save(product);
        eventPublisher.publishEvent(new ProductCreatedEvent(product.getId(), product.getName(), product.getDescription(), product.getPrice()));
        return product;
    }

    @Transactional
    public Product handle(UpdateProductCommand command) {
        Product product = productRepository.findById(command.getProductId())
                .orElseThrow(() -> new IllegalArgumentException("Product not found: " + command.getProductId()));
        product.update(command.getName(), command.getDescription(), command.getPrice());
        productRepository.save(product);
        eventPublisher.publishEvent(new ProductUpdatedEvent(product.getId(), product.getName(), product.getDescription(), product.getPrice()));
        return product;
    }

    // TODO: Add more command handlers as needed (e.g., DeleteProductCommand)
}