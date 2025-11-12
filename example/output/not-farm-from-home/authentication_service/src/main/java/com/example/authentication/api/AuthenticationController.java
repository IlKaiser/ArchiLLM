package com.example.authentication.api;

import com.example.authentication.domain.AuthenticationService;
import com.example.authentication.domain.AuthenticationRequest;
import com.example.authentication.domain.AuthenticationResult;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthenticationController {

    private final AuthenticationService authenticationService;

    @Autowired
    public AuthenticationController(AuthenticationService authenticationService) {
        this.authenticationService = authenticationService;
    }

    @PostMapping("/login")
    public ResponseEntity<AuthenticationResult> login(@RequestBody AuthenticationRequest request) {
        AuthenticationResult result = authenticationService.authenticate(request);
        if (result.isAuthenticated()) {
            return ResponseEntity.ok(result);
        } else {
            return ResponseEntity.status(401).body(result);
        }
    }

    // TODO: Add more endpoints (e.g., logout, register) as needed.
}