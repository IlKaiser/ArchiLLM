package com.example.product.controller;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/products")
public class ProductController {
    private static final Map<String, Map<String, Object>> products = new HashMap<>();
    private static int idCounter = 1;

    @PostMapping
    public Map<String, Object> addProduct(@RequestBody Map<String, Object> payload) {
        String id = String.valueOf(idCounter++);
        products.put(id, payload);
        // Simulate domain event emission
        return Map.of("product_id", id, "add_result", "success");
    }

    @PutMapping("/{product_id}")
    public Map<String, Object> updateProduct(@PathVariable String product_id, @RequestBody Map<String, Object> updates) {
        if (products.containsKey(product_id)) {
            products.get(product_id).putAll(updates);
            // Simulate domain event emission
            return Map.of("update_result", "success");
        }
        return Map.of("update_result", "not found");
    }

    @DeleteMapping("/{product_id}")
    public Map<String, Object> deleteProduct(@PathVariable String product_id) {
        products.remove(product_id);
        // Simulate domain event emission
        return Map.of("delete_result", "success");
    }

    @GetMapping("/hot")
    public Map<String, Object> getHotProducts(@RequestParam(required = false) String season, @RequestParam(required = false) String area) {
        // Simulate hot product logic
        return Map.of("hot_product_list", products.values());
    }
}