package com.example.catalog.api;

import com.example.catalog.command.CatalogService;
import com.example.catalog.command.ProductCommand;
import com.example.catalog.query.ProductQueryService;
import com.example.catalog.query.ProductView;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;

@RestController
@RequestMapping("/products")
public class ProductController {

    private final CatalogService catalogService;
    private final ProductQueryService productQueryService;

    public ProductController(CatalogService catalogService, ProductQueryService productQueryService) {
        this.catalogService = catalogService;
        this.productQueryService = productQueryService;
    }

    // CQRS: Command - create product
    @PostMapping
    public ResponseEntity<Void> createProduct(@RequestBody ProductCommand.CreateProductRequest request) {
        Long productId = catalogService.createProduct(request);
        // TODO: Publish ProductCreatedEvent
        return ResponseEntity.created(URI.create("/products/" + productId)).build();
    }

    // CQRS: Command - update product
    @PutMapping("/{id}")
    public ResponseEntity<Void> updateProduct(@PathVariable Long id, @RequestBody ProductCommand.UpdateProductRequest request) {
        catalogService.updateProduct(id, request);
        // TODO: Publish ProductUpdatedEvent
        return ResponseEntity.noContent().build();
    }

    // CQRS: Query - get product by id
    @GetMapping("/{id}")
    public ResponseEntity<ProductView> getProduct(@PathVariable Long id) {
        ProductView product = productQueryService.getProductById(id);
        if (product == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(product);
    }

    // CQRS: Query - list products
    @GetMapping
    public List<ProductView> listProducts() {
        return productQueryService.listProducts();
    }
}