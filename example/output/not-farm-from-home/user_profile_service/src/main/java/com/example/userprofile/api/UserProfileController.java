package com.example.userprofile.api;

import com.example.userprofile.domain.UserProfile;
import com.example.userprofile.service.UserProfileService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/user-profiles")
public class UserProfileController {

    private final UserProfileService userProfileService;

    @Autowired
    public UserProfileController(UserProfileService userProfileService) {
        this.userProfileService = userProfileService;
    }

    @GetMapping("/{id}")
    public UserProfile getUserProfile(@PathVariable Long id) {
        return userProfileService.findById(id);
    }

    @PostMapping
    public UserProfile createUserProfile(@RequestBody UserProfile userProfile) {
        return userProfileService.createUserProfile(userProfile);
    }

    @PutMapping("/{id}")
    public UserProfile updateUserProfile(@PathVariable Long id, @RequestBody UserProfile userProfile) {
        return userProfileService.updateUserProfile(id, userProfile);
    }

    @GetMapping
    public List<UserProfile> listUserProfiles() {
        // In a real API composition scenario, this might aggregate data from other services.
        // TODO: Compose data from other services if needed.
        return userProfileService.findAll();
    }
}