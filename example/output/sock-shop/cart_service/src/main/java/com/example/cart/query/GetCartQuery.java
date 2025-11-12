package com.example.cart.query;

import java.util.Objects;

public class GetCartQuery {
    private final Long cartId;

    public GetCartQuery(Long cartId) {
        this.cartId = cartId;
    }

    public Long getCartId() {
        return cartId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof GetCartQuery)) return false;
        GetCartQuery that = (GetCartQuery) o;
        return Objects.equals(cartId, that.cartId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(cartId);
    }

    @Override
    public String toString() {
        return "GetCartQuery{" +
                "cartId=" + cartId +
                '}';
    }
}