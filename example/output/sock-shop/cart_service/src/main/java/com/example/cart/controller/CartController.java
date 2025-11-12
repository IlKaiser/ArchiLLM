package com.example.cart.controller;

import com.example.cart.model.Cart;
import com.example.cart.model.CartItem;
import com.example.cart.service.CartService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/cart")
public class CartController {
    @Autowired
    private CartService cartService;

    @GetMapping("/{userId}")
    public ResponseEntity<Cart> getCart(@PathVariable String userId) {
        return ResponseEntity.ok(cartService.getCart(userId));
    }

    @PostMapping("/{userId}/items")
    public ResponseEntity<Cart> addItem(@PathVariable String userId, @RequestBody CartItem item) {
        return ResponseEntity.ok(cartService.addItem(userId, item));
    }

    @PutMapping("/{userId}/items/{productId}")
    public ResponseEntity<Cart> updateItem(@PathVariable String userId, @PathVariable Long productId, @RequestBody CartItem item) {
        return ResponseEntity.ok(cartService.updateItem(userId, productId, item.getQuantity()));
    }

    @DeleteMapping("/{userId}/items/{productId}")
    public ResponseEntity<Cart> removeItem(@PathVariable String userId, @PathVariable Long productId) {
        return ResponseEntity.ok(cartService.removeItem(userId, productId));
    }
}