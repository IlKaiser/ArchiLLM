package com.example.product.api;

import com.example.product.domain.Product;
import com.example.product.service.ProductCatalogService;
import com.example.product.events.ProductEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductCatalogService productCatalogService;
    private final ApplicationEventPublisher eventPublisher;

    @Autowired
    public ProductController(ProductCatalogService productCatalogService,
                             ApplicationEventPublisher eventPublisher) {
        this.productCatalogService = productCatalogService;
        this.eventPublisher = eventPublisher;
    }

    @GetMapping
    public List<Product> listProducts() {
        return productCatalogService.findAll();
    }

    @GetMapping("/{id}")
    public ResponseEntity<Product> getProduct(@PathVariable Long id) {
        return productCatalogService.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<Product> createProduct(@RequestBody Product product) {
        Product created = productCatalogService.createProduct(product);
        // Publish domain event
        eventPublisher.publishEvent(new ProductEvent.ProductCreatedEvent(created.getId()));
        return ResponseEntity.ok(created);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Product> updateProduct(@PathVariable Long id, @RequestBody Product product) {
        return productCatalogService.updateProduct(id, product)
                .map(updated -> {
                    eventPublisher.publishEvent(new ProductEvent.ProductUpdatedEvent(id));
                    return ResponseEntity.ok(updated);
                })
                .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteProduct(@PathVariable Long id) {
        boolean deleted = productCatalogService.deleteProduct(id);
        if (deleted) {
            eventPublisher.publishEvent(new ProductEvent.ProductDeletedEvent(id));
            return ResponseEntity.noContent().build();
        } else {
            return ResponseEntity.notFound().build();
        }
    }

    // TODO: API composition endpoints for aggregating product info with other services

    // TODO: Integrate with Order saga for product reservation/stock management

}