package com.example.admin.service;

import com.example.admin.domain.Admin;
import com.example.admin.domain.AdminEvent;
import com.example.admin.domain.AdminRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
public class AdminService {

    private final AdminRepository adminRepository;
    // TODO: Inject event publisher for domain events

    public AdminService(AdminRepository adminRepository) {
        this.adminRepository = adminRepository;
    }

    @Transactional
    public Admin registerAdmin(String username, String email) {
        Admin admin = Admin.create(username, email);
        adminRepository.save(admin);
        // TODO: Publish AdminCreatedEvent
        return admin;
    }

    @Transactional
    public void deactivateAdmin(Long adminId) {
        Optional<Admin> adminOpt = adminRepository.findById(adminId);
        if (adminOpt.isPresent()) {
            Admin admin = adminOpt.get();
            admin.deactivate();
            adminRepository.save(admin);
            // TODO: Publish AdminDeactivatedEvent
        } else {
            throw new IllegalArgumentException("Admin not found: " + adminId);
        }
    }

    public Optional<Admin> findAdmin(Long adminId) {
        return adminRepository.findById(adminId);
    }
}