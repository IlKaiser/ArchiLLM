package com.example.cart.domain;

import java.util.Collections;
import java.util.List;
import java.util.ArrayList;
import java.util.Objects;

/**
 * Aggregate root representing a shopping cart.
 */
public class Cart {

    private final Long id;
    private final Long customerId;
    private final List<CartItem> items;

    public Cart(Long id, Long customerId) {
        this.id = id;
        this.customerId = customerId;
        this.items = new ArrayList<>();
    }

    public Long getId() {
        return id;
    }

    public Long getCustomerId() {
        return customerId;
    }

    public List<CartItem> getItems() {
        return Collections.unmodifiableList(items);
    }

    public void addItem(Long productId, int quantity) {
        Objects.requireNonNull(productId, "productId must not be null");
        if (quantity <= 0) throw new IllegalArgumentException("quantity must be positive");
        for (CartItem item : items) {
            if (item.getProductId().equals(productId)) {
                item.increaseQuantity(quantity);
                return;
            }
        }
        items.add(new CartItem(productId, quantity));
    }

    public void removeItem(Long productId) {
        Objects.requireNonNull(productId, "productId must not be null");
        items.removeIf(item -> item.getProductId().equals(productId));
    }

    public void changeItemQuantity(Long productId, int newQuantity) {
        Objects.requireNonNull(productId, "productId must not be null");
        if (newQuantity < 0) throw new IllegalArgumentException("quantity must not be negative");
        for (CartItem item : items) {
            if (item.getProductId().equals(productId)) {
                if (newQuantity == 0) {
                    items.remove(item);
                } else {
                    item.setQuantity(newQuantity);
                }
                return;
            }
        }
        if (newQuantity > 0) {
            items.add(new CartItem(productId, newQuantity));
        }
    }

    // TODO: Add domain methods for checkout, etc.

    /**
     * Value object representing an item in the cart.
     */
    public static class CartItem {
        private final Long productId;
        private int quantity;

        public CartItem(Long productId, int quantity) {
            this.productId = Objects.requireNonNull(productId);
            if (quantity <= 0) throw new IllegalArgumentException("quantity must be positive");
            this.quantity = quantity;
        }

        public Long getProductId() {
            return productId;
        }

        public int getQuantity() {
            return quantity;
        }

        void increaseQuantity(int delta) {
            if (delta <= 0) throw new IllegalArgumentException("delta must be positive");
            this.quantity += delta;
        }

        void setQuantity(int quantity) {
            if (quantity <= 0) throw new IllegalArgumentException("quantity must be positive");
            this.quantity = quantity;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof CartItem)) return false;
            CartItem cartItem = (CartItem) o;
            return Objects.equals(productId, cartItem.productId);
        }

        @Override
        public int hashCode() {
            return Objects.hash(productId);
        }
    }
}