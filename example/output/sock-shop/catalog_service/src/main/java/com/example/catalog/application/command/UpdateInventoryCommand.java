package com.example.catalog.application.command;

import java.util.Objects;

public class UpdateInventoryCommand {

    private final Long productId;
    private final int quantityDelta;

    public UpdateInventoryCommand(Long productId, int quantityDelta) {
        this.productId = productId;
        this.quantityDelta = quantityDelta;
    }

    public Long getProductId() {
        return productId;
    }

    public int getQuantityDelta() {
        return quantityDelta;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof UpdateInventoryCommand)) return false;
        UpdateInventoryCommand that = (UpdateInventoryCommand) o;
        return quantityDelta == that.quantityDelta &&
                Objects.equals(productId, that.productId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(productId, quantityDelta);
    }

    @Override
    public String toString() {
        return "UpdateInventoryCommand{" +
                "productId=" + productId +
                ", quantityDelta=" + quantityDelta +
                '}';
    }
}