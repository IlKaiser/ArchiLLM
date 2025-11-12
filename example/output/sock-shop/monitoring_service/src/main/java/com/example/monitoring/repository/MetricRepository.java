package com.example.monitoring.repository;

import com.example.monitoring.model.Metric;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MetricRepository extends JpaRepository<Metric, Long> {
}