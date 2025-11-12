package com.example.logging;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class LoggingServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(LoggingServiceApplication.class, args);
    }

    // TODO: Implement event publishing and handling logic as per business requirements.
    // This service uses domain events but does not implement aggregates or CQRS.
    // Integrate with messaging/event bus as needed.
}