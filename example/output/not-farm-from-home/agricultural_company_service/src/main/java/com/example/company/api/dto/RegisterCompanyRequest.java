package com.example.company.api.dto;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

public class RegisterCompanyRequest {

    @NotBlank
    @Size(max = 100)
    private String name;

    @NotBlank
    @Size(max = 255)
    private String address;

    @NotBlank
    @Size(max = 50)
    private String registrationNumber;

    public RegisterCompanyRequest() {
    }

    public RegisterCompanyRequest(String name, String address, String registrationNumber) {
        this.name = name;
        this.address = address;
        this.registrationNumber = registrationNumber;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getRegistrationNumber() {
        return registrationNumber;
    }

    public void setRegistrationNumber(String registrationNumber) {
        this.registrationNumber = registrationNumber;
    }
}