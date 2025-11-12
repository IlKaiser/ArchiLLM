package com.example.cart.domain;

import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;

public class Cart {

    private final UUID id;
    private final List<CartItem> items = new CopyOnWriteArrayList<>();
    private final List<CartEvent> pendingEvents = new ArrayList<>();

    public Cart(UUID id) {
        this.id = id;
    }

    public UUID getId() {
        return id;
    }

    public List<CartItem> getItems() {
        return Collections.unmodifiableList(items);
    }

    public List<CartEvent> getPendingEvents() {
        return Collections.unmodifiableList(pendingEvents);
    }

    public void addItem(String productId, int quantity) {
        Optional<CartItem> existing = items.stream()
                .filter(i -> i.getProductId().equals(productId))
                .findFirst();
        if (existing.isPresent()) {
            CartItem item = existing.get();
            item.increaseQuantity(quantity);
        } else {
            items.add(new CartItem(productId, quantity));
        }
        pendingEvents.add(new ItemAddedEvent(id, productId, quantity));
    }

    public void removeItem(String productId) {
        items.removeIf(i -> i.getProductId().equals(productId));
        pendingEvents.add(new ItemRemovedEvent(id, productId));
    }

    public void clear() {
        items.clear();
        pendingEvents.add(new CartClearedEvent(id));
    }

    public void markEventsAsPublished() {
        pendingEvents.clear();
    }

    // Aggregate child entity
    public static class CartItem {
        private final String productId;
        private int quantity;

        public CartItem(String productId, int quantity) {
            this.productId = productId;
            this.quantity = quantity;
        }

        public String getProductId() {
            return productId;
        }

        public int getQuantity() {
            return quantity;
        }

        public void increaseQuantity(int delta) {
            this.quantity += delta;
        }
    }

    // Domain events
    public interface CartEvent {}

    public static class ItemAddedEvent implements CartEvent {
        private final UUID cartId;
        private final String productId;
        private final int quantity;

        public ItemAddedEvent(UUID cartId, String productId, int quantity) {
            this.cartId = cartId;
            this.productId = productId;
            this.quantity = quantity;
        }

        public UUID getCartId() {
            return cartId;
        }

        public String getProductId() {
            return productId;
        }

        public int getQuantity() {
            return quantity;
        }
    }

    public static class ItemRemovedEvent implements CartEvent {
        private final UUID cartId;
        private final String productId;

        public ItemRemovedEvent(UUID cartId, String productId) {
            this.cartId = cartId;
            this.productId = productId;
        }

        public UUID getCartId() {
            return cartId;
        }

        public String getProductId() {
            return productId;
        }
    }

    public static class CartClearedEvent implements CartEvent {
        private final UUID cartId;

        public CartClearedEvent(UUID cartId) {
            this.cartId = cartId;
        }

        public UUID getCartId() {
            return cartId;
        }
    }
}