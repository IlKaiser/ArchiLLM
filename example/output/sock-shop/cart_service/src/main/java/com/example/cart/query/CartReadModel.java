package com.example.cart.query;

import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * Read model for Cart, optimized for queries (CQRS read side).
 */
public class CartReadModel {

    private final Long cartId;
    private final Long customerId;
    private final List<CartItemReadModel> items;
    private final double totalPrice;

    public CartReadModel(Long cartId, Long customerId, List<CartItemReadModel> items, double totalPrice) {
        this.cartId = cartId;
        this.customerId = customerId;
        this.items = items != null ? Collections.unmodifiableList(items) : Collections.emptyList();
        this.totalPrice = totalPrice;
    }

    public Long getCartId() {
        return cartId;
    }

    public Long getCustomerId() {
        return customerId;
    }

    public List<CartItemReadModel> getItems() {
        return items;
    }

    public double getTotalPrice() {
        return totalPrice;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof CartReadModel)) return false;
        CartReadModel that = (CartReadModel) o;
        return Double.compare(that.totalPrice, totalPrice) == 0 &&
                Objects.equals(cartId, that.cartId) &&
                Objects.equals(customerId, that.customerId) &&
                Objects.equals(items, that.items);
    }

    @Override
    public int hashCode() {
        return Objects.hash(cartId, customerId, items, totalPrice);
    }

    @Override
    public String toString() {
        return "CartReadModel{" +
                "cartId=" + cartId +
                ", customerId=" + customerId +
                ", items=" + items +
                ", totalPrice=" + totalPrice +
                '}';
    }

    /**
     * Read model for a cart item.
     */
    public static class CartItemReadModel {
        private final Long productId;
        private final String productName;
        private final int quantity;
        private final double price;

        public CartItemReadModel(Long productId, String productName, int quantity, double price) {
            this.productId = productId;
            this.productName = productName;
            this.quantity = quantity;
            this.price = price;
        }

        public Long getProductId() {
            return productId;
        }

        public String getProductName() {
            return productName;
        }

        public int getQuantity() {
            return quantity;
        }

        public double getPrice() {
            return price;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof CartItemReadModel)) return false;
            CartItemReadModel that = (CartItemReadModel) o;
            return quantity == that.quantity &&
                    Double.compare(that.price, price) == 0 &&
                    Objects.equals(productId, that.productId) &&
                    Objects.equals(productName, that.productName);
        }

        @Override
        public int hashCode() {
            return Objects.hash(productId, productName, quantity, price);
        }

        @Override
        public String toString() {
            return "CartItemReadModel{" +
                    "productId=" + productId +
                    ", productName='" + productName + '\'' +
                    ", quantity=" + quantity +
                    ", price=" + price +
                    '}';
        }
    }
}