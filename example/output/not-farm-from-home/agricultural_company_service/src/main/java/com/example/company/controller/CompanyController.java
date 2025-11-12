package com.example.company.controller;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/companies")
public class CompanyController {
    private static final Map<String, Map<String, Object>> companies = new HashMap<>();
    private static int idCounter = 1;

    @PostMapping
    public Map<String, Object> registerCompany(@RequestBody Map<String, Object> payload) {
        String id = String.valueOf(idCounter++);
        companies.put(id, payload);
        return Map.of("company_id", id, "registration_result", "success");
    }

    @GetMapping
    public Map<String, Object> listCompanies(@RequestParam(required = false) String area, @RequestParam(required = false) String filters) {
        return Map.of("company_list", companies.values());
    }

    @GetMapping("/{company_id}/location")
    public Map<String, Object> getLocation(@PathVariable String company_id) {
        Map<String, Object> company = companies.get(company_id);
        String location = company != null ? (String) company.getOrDefault("location", "Unknown") : "Unknown";
        String url = "https://maps.google.com/?q=" + location.replace(" ", "+");
        return Map.of("location_url", url);
    }
}