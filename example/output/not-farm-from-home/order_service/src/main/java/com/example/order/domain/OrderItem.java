package com.example.order.domain;

import java.util.Objects;
import java.math.BigDecimal;

/**
 * Value object representing an item within an order.
 */
public class OrderItem {

    private final Long menuItemId;
    private final String name;
    private final BigDecimal price;
    private final int quantity;

    public OrderItem(Long menuItemId, String name, BigDecimal price, int quantity) {
        this.menuItemId = menuItemId;
        this.name = name;
        this.price = price;
        this.quantity = quantity;
    }

    public Long getMenuItemId() {
        return menuItemId;
    }

    public String getName() {
        return name;
    }

    public BigDecimal getPrice() {
        return price;
    }

    public int getQuantity() {
        return quantity;
    }

    public BigDecimal getTotalPrice() {
        return price.multiply(BigDecimal.valueOf(quantity));
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof OrderItem)) return false;
        OrderItem that = (OrderItem) o;
        return quantity == that.quantity &&
                Objects.equals(menuItemId, that.menuItemId) &&
                Objects.equals(name, that.name) &&
                Objects.equals(price, that.price);
    }

    @Override
    public int hashCode() {
        return Objects.hash(menuItemId, name, price, quantity);
    }

    @Override
    public String toString() {
        return "OrderItem{" +
                "menuItemId=" + menuItemId +
                ", name='" + name + '\'' +
                ", price=" + price +
                ", quantity=" + quantity +
                '}';
    }
}