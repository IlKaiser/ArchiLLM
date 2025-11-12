package com.example.userprofile.application;

import com.example.userprofile.domain.UserProfile;
import com.example.userprofile.domain.UserProfileRepository;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.Optional;

@Service
public class UserProfileService {

    private final UserProfileRepository userProfileRepository;

    @Autowired
    public UserProfileService(UserProfileRepository userProfileRepository) {
        this.userProfileRepository = userProfileRepository;
    }

    public UserProfile createUserProfile(String userId, String name, String email) {
        UserProfile userProfile = new UserProfile(userId, name, email);
        return userProfileRepository.save(userProfile);
    }

    public Optional<UserProfile> findUserProfile(String userId) {
        return userProfileRepository.findById(userId);
    }

    public UserProfile updateUserProfile(String userId, String name, String email) {
        Optional<UserProfile> optional = userProfileRepository.findById(userId);
        if (optional.isPresent()) {
            UserProfile userProfile = optional.get();
            userProfile.setName(name);
            userProfile.setEmail(email);
            return userProfileRepository.save(userProfile);
        } else {
            throw new UserProfileNotFoundException(userId);
        }
    }

    public void deleteUserProfile(String userId) {
        userProfileRepository.deleteById(userId);
    }

    // TODO: Integrate with other services for API composition as needed.
}