package com.example.admin.controller;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/admin")
public class AdminController {
    @DeleteMapping("/users/{user_id}")
    public Map<String, Object> deleteUser(@PathVariable String user_id, @RequestParam String admin_id, @RequestParam String session_token) {
        // Simulate user deletion and domain event emission
        return Map.of("delete_result", "success");
    }
}