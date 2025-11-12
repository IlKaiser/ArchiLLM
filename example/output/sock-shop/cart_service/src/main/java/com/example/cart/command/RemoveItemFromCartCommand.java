package com.example.cart.command;

import java.util.Objects;

public class RemoveItemFromCartCommand {

    private final String cartId;
    private final String itemId;

    public RemoveItemFromCartCommand(String cartId, String itemId) {
        this.cartId = cartId;
        this.itemId = itemId;
    }

    public String getCartId() {
        return cartId;
    }

    public String getItemId() {
        return itemId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof RemoveItemFromCartCommand)) return false;
        RemoveItemFromCartCommand that = (RemoveItemFromCartCommand) o;
        return Objects.equals(cartId, that.cartId) &&
                Objects.equals(itemId, that.itemId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(cartId, itemId);
    }

    @Override
    public String toString() {
        return "RemoveItemFromCartCommand{" +
                "cartId='" + cartId + '\'' +
                ", itemId='" + itemId + '\'' +
                '}';
    }
}