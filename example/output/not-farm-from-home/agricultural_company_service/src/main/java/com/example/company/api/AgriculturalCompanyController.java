package com.example.company.api;

import com.example.company.domain.AgriculturalCompany;
import com.example.company.service.AgriculturalCompanyService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/companies")
public class AgriculturalCompanyController {

    private final AgriculturalCompanyService companyService;

    public AgriculturalCompanyController(AgriculturalCompanyService companyService) {
        this.companyService = companyService;
    }

    @PostMapping
    public ResponseEntity<AgriculturalCompany> registerCompany(@RequestBody AgriculturalCompany company) {
        AgriculturalCompany created = companyService.registerCompany(company);
        return ResponseEntity.ok(created);
    }

    @GetMapping("/{id}")
    public ResponseEntity<AgriculturalCompany> getCompany(@PathVariable Long id) {
        return companyService.getCompany(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    public List<AgriculturalCompany> listCompanies() {
        return companyService.listCompanies();
    }
}