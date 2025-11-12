package com.example.order.repository;

import com.example.order.domain.Order;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    // TODO: Add custom query methods if needed
}