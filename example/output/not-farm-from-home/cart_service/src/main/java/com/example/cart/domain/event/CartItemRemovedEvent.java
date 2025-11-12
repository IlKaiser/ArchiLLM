package com.example.cart.domain.event;

import java.util.Objects;

public class CartItemRemovedEvent {

    private final String cartId;
    private final String itemId;
    private final int quantity;

    public CartItemRemovedEvent(String cartId, String itemId, int quantity) {
        this.cartId = cartId;
        this.itemId = itemId;
        this.quantity = quantity;
    }

    public String getCartId() {
        return cartId;
    }

    public String getItemId() {
        return itemId;
    }

    public int getQuantity() {
        return quantity;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof CartItemRemovedEvent)) return false;
        CartItemRemovedEvent that = (CartItemRemovedEvent) o;
        return quantity == that.quantity &&
                Objects.equals(cartId, that.cartId) &&
                Objects.equals(itemId, that.itemId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(cartId, itemId, quantity);
    }

    @Override
    public String toString() {
        return "CartItemRemovedEvent{" +
                "cartId='" + cartId + '\'' +
                ", itemId='" + itemId + '\'' +
                ", quantity=" + quantity +
                '}';
    }
}