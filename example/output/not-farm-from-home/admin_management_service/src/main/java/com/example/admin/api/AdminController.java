package com.example.admin.api;

import com.example.admin.domain.Admin;
import com.example.admin.domain.AdminEvent;
import com.example.admin.service.AdminManagementService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/admins")
public class AdminController {

    private final AdminManagementService adminManagementService;

    public AdminController(AdminManagementService adminManagementService) {
        this.adminManagementService = adminManagementService;
    }

    @PostMapping
    public ResponseEntity<Admin> createAdmin(@RequestBody CreateAdminRequest request) {
        Admin admin = adminManagementService.createAdmin(request.getName(), request.getEmail());
        return ResponseEntity.ok(admin);
    }

    @GetMapping("/{adminId}")
    public ResponseEntity<Admin> getAdmin(@PathVariable Long adminId) {
        Admin admin = adminManagementService.getAdmin(adminId);
        if (admin == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(admin);
    }

    @PostMapping("/{adminId}/deactivate")
    public ResponseEntity<Admin> deactivateAdmin(@PathVariable Long adminId) {
        Admin admin = adminManagementService.deactivateAdmin(adminId);
        if (admin == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(admin);
    }

    @GetMapping("/{adminId}/events")
    public ResponseEntity<List<AdminEvent>> getAdminEvents(@PathVariable Long adminId) {
        List<AdminEvent> events = adminManagementService.getAdminEvents(adminId);
        return ResponseEntity.ok(events);
    }

    // DTO for create request
    public static class CreateAdminRequest {
        private String name;
        private String email;

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getEmail() {
            return email;
        }

        public void setEmail(String email) {
            this.email = email;
        }
    }
}