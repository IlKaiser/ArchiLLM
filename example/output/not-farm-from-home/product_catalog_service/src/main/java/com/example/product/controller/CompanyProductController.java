package com.example.product.controller;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/companies/{company_id}/products")
public class CompanyProductController {
    @GetMapping
    public Map<String, Object> listCompanyProducts(@PathVariable String company_id, @RequestParam(required = false) String filters) {
        // For demo, return all products (should filter by company_id)
        return Map.of("product_list", List.of());
    }
}