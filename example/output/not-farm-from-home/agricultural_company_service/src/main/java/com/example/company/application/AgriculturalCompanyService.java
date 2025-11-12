package com.example.company.application;

import com.example.company.domain.AgriculturalCompany;
import com.example.company.domain.AgriculturalCompanyRepository;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.Optional;
import java.util.List;

@Service
public class AgriculturalCompanyService {

    private final AgriculturalCompanyRepository companyRepository;

    @Autowired
    public AgriculturalCompanyService(AgriculturalCompanyRepository companyRepository) {
        this.companyRepository = companyRepository;
    }

    public AgriculturalCompany registerCompany(String name, String address) {
        // Business logic for registration
        AgriculturalCompany company = new AgriculturalCompany(name, address);
        return companyRepository.save(company);
    }

    public Optional<AgriculturalCompany> findCompanyById(Long id) {
        return companyRepository.findById(id);
    }

    public List<AgriculturalCompany> listAllCompanies() {
        return companyRepository.findAll();
    }

    public AgriculturalCompany updateCompany(Long id, String name, String address) {
        Optional<AgriculturalCompany> optional = companyRepository.findById(id);
        if (optional.isPresent()) {
            AgriculturalCompany company = optional.get();
            company.setName(name);
            company.setAddress(address);
            return companyRepository.save(company);
        } else {
            throw new IllegalArgumentException("Company not found");
        }
    }

    public void deleteCompany(Long id) {
        companyRepository.deleteById(id);
    }

    // TODO: Integrate with other services via API composition if needed
    // e.g., fetch related data from other microservices
}