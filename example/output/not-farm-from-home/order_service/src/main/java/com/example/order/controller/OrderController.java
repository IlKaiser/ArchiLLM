package com.example.order.controller;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/orders")
public class OrderController {
    private static final Map<String, Map<String, Object>> orders = new HashMap<>();
    private static int idCounter = 1;

    @PostMapping
    public Map<String, Object> createOrder(@RequestBody Map<String, Object> payload) {
        String id = String.valueOf(idCounter++);
        orders.put(id, payload);
        // Simulate saga and domain event emission
        return Map.of("order_id", id, "order_result", "success");
    }

    @GetMapping("/{order_id}")
    public Map<String, Object> getOrder(@PathVariable String order_id, @RequestParam String user_id) {
        return Map.of("order_details", orders.getOrDefault(order_id, Map.of()));
    }
}