package com.example.cart.controller;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/cart")
public class CartController {
    private static final Map<String, List<Map<String, Object>>> carts = new HashMap<>();

    @GetMapping
    public Map<String, Object> getCart(@RequestParam String user_id, @RequestParam String session_token) {
        return Map.of("cart_contents", carts.getOrDefault(user_id, List.of()));
    }

    @PostMapping("/add")
    public Map<String, Object> addToCart(@RequestBody Map<String, Object> payload) {
        String user_id = (String) payload.get("user_id");
        Map<String, Object> item = Map.of(
            "product_id", payload.get("product_id"),
            "quantity", payload.get("quantity")
        );
        carts.computeIfAbsent(user_id, k -> new ArrayList<>()).add(item);
        // Simulate domain event emission
        return Map.of("add_result", "success");
    }

    @PostMapping("/remove")
    public Map<String, Object> removeFromCart(@RequestBody Map<String, Object> payload) {
        String user_id = (String) payload.get("user_id");
        String product_id = (String) payload.get("product_id");
        List<Map<String, Object>> cart = carts.getOrDefault(user_id, new ArrayList<>());
        cart.removeIf(item -> product_id.equals(item.get("product_id")));
        // Simulate domain event emission
        return Map.of("remove_result", "success");
    }
}