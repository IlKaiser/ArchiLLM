package com.example.cart.command;

import java.util.Objects;

public class AddItemToCartCommand {

    private Long cartId;
    private Long productId;
    private int quantity;

    public AddItemToCartCommand() {
    }

    public AddItemToCartCommand(Long cartId, Long productId, int quantity) {
        this.cartId = cartId;
        this.productId = productId;
        this.quantity = quantity;
    }

    public Long getCartId() {
        return cartId;
    }

    public void setCartId(Long cartId) {
        this.cartId = cartId;
    }

    public Long getProductId() {
        return productId;
    }

    public void setProductId(Long productId) {
        this.productId = productId;
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof AddItemToCartCommand)) return false;
        AddItemToCartCommand that = (AddItemToCartCommand) o;
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
        return "AddItemToCartCommand{" +
                "cartId=" + cartId +
                ", productId=" + productId +
                ", quantity=" + quantity +
                '}';
    }
}