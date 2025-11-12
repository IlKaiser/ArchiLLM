package com.example.product.composition;

import com.example.product.domain.Product;
import com.example.product.service.ProductCatalogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Optional;

/**
 * Composes product data with other services for API composition.
 * This is a stub; integration with other services (e.g., Order, Inventory) is TODO.
 */
@Service
public class ProductApiComposer {

    private final ProductCatalogService productCatalogService;

    @Autowired
    public ProductApiComposer(ProductCatalogService productCatalogService) {
        this.productCatalogService = productCatalogService;
    }

    /**
     * Compose product details with data from other services.
     * @param productId the product id
     * @return composed product view
     */
    public Optional<ProductView> getComposedProductView(Long productId) {
        Optional<Product> productOpt = productCatalogService.findById(productId);
        if (productOpt.isEmpty()) {
            return Optional.empty();
        }
        Product product = productOpt.get();

        // TODO: Integrate with Order service (e.g., to show order status for this product)
        // TODO: Integrate with Inventory service (e.g., to show stock level)
        // TODO: Integrate with Pricing service (if separate)

        ProductView view = new ProductView();
        view.setId(product.getId());
        view.setName(product.getName());
        view.setDescription(product.getDescription());
        view.setPrice(product.getPrice());

        // TODO: Set additional fields from other services

        return Optional.of(view);
    }

    /**
     * DTO for composed product view.
     */
    public static class ProductView {
        private Long id;
        private String name;
        private String description;
        private Double price;

        // TODO: Add fields for order status, inventory, etc.

        public Long getId() {
            return id;
        }

        public void setId(Long id) {
            this.id = id;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getDescription() {
            return description;
        }

        public void setDescription(String description) {
            this.description = description;
        }

        public Double getPrice() {
            return price;
        }

        public void setPrice(Double price) {
            this.price = price;
        }
    }
}