package com.example.company.domain;

import org.springframework.data.repository.CrudRepository;

// Repository interface for managing AgriculturalCompany aggregates
public interface AgriculturalCompanyRepository extends CrudRepository<AgriculturalCompany, Long> {
    // Additional query methods can be defined here if needed
}