package com.example.company.api;

import com.example.company.domain.AgriculturalCompany;
import com.example.company.domain.Product;
import com.example.company.service.AgriculturalCompanyService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

/**
 * REST controller for API composition endpoints.
 * Aggregates company and product data.
 */
@RestController
public class ApiCompositionController {

    private final AgriculturalCompanyService companyService;

    public ApiCompositionController(AgriculturalCompanyService companyService) {
        this.companyService = companyService;
    }

    /**
     * Example API composition endpoint: get company and its products.
     */
    @GetMapping("/api/companies/{companyId}/details")
    public Map<String, Object> getCompanyWithProducts(@PathVariable Long companyId) {
        Map<String, Object> result = new HashMap<>();
        AgriculturalCompany company = companyService.findById(companyId);
        result.put("company", company);

        // TODO: Integrate with ProductService or repository to fetch products for the company
        List<Product> products = companyService.findProductsByCompanyId(companyId);
        result.put("products", products);

        return result;
    }
}