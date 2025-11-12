package com.example.cart.controller;

import com.example.cart.service.CartService;
import com.example.cart.domain.Cart;
import com.example.cart.domain.CartItem;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/carts")
public class CartCommandController {

    private final CartService cartService;

    public CartCommandController(CartService cartService) {
        this.cartService = cartService;
    }

    @PostMapping
    public ResponseEntity<Cart> createCart() {
        Cart cart = cartService.createCart();
        return ResponseEntity.ok(cart);
    }

    @PostMapping("/{cartId}/items")
    public ResponseEntity<Cart> addItem(
            @PathVariable Long cartId,
            @RequestBody AddItemRequest request) {
        Cart cart = cartService.addItem(cartId, request.getProductId(), request.getQuantity());
        return ResponseEntity.ok(cart);
    }

    @DeleteMapping("/{cartId}/items/{productId}")
    public ResponseEntity<Cart> removeItem(
            @PathVariable Long cartId,
            @PathVariable Long productId) {
        Cart cart = cartService.removeItem(cartId, productId);
        return ResponseEntity.ok(cart);
    }

    @PostMapping("/{cartId}/checkout")
    public ResponseEntity<Void> checkout(@PathVariable Long cartId) {
        // TODO: Integrate with order service, payment, etc.
        cartService.checkout(cartId);
        return ResponseEntity.ok().build();
    }

    // DTO for add item request
    public static class AddItemRequest {
        private Long productId;
        private int quantity;

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
    }
}