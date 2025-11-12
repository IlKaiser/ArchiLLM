package com.example.monitoring.repository;

import com.example.monitoring.model.Alert;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AlertRepository extends JpaRepository<Alert, Long> {
}