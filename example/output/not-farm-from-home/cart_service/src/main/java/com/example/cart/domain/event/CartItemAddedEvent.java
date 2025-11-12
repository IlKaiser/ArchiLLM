package com.example.cart.domain.event;

import java.util.Objects;

public class CartItemAddedEvent {

    private final String cartId;
    private final String productId;
    private final int quantity;

    public CartItemAddedEvent(String cartId, String productId, int quantity) {
        this.cartId = cartId;
        this.productId = productId;
        this.quantity = quantity;
    }

    public String getCartId() {
        return cartId;
    }

    public String getProductId() {
        return productId;
    }

    public int getQuantity() {
        return quantity;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof CartItemAddedEvent)) return false;
        CartItemAddedEvent that = (CartItemAddedEvent) o;
        return quantity == that.quantity &&
                Objects.equals(cartId, that.cartId) &&
                Objects.equals(productId, that.productId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(cartId, productId, quantity);
    }

    @Override
    public String toString() {
        return "CartItemAddedEvent{" +
                "cartId='" + cartId + '\'' +
                ", productId='" + productId + '\'' +
                ", quantity=" + quantity +
                '}';
    }
}