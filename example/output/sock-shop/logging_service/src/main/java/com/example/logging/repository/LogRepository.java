package com.example.logging.repository;

import com.example.logging.model.LogEvent;
import org.springframework.data.jpa.repository.JpaRepository;

public interface LogRepository extends JpaRepository<LogEvent, Long> {
}