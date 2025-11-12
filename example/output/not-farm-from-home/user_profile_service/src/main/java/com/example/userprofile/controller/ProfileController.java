package com.example.userprofile.controller;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/profile")
public class ProfileController {
    private static final Map<String, Map<String, Object>> profiles = new HashMap<>();

    @GetMapping
    public Map<String, Object> getProfile(@RequestParam String user_id, @RequestParam String session_token) {
        return profiles.getOrDefault(user_id, Map.of("profile_data", "not found"));
    }

    @PutMapping
    public Map<String, Object> updateProfile(@RequestParam String user_id, @RequestParam String session_token, @RequestBody Map<String, Object> updates) {
        profiles.put(user_id, updates);
        return Map.of("update_result", "success");
    }
}