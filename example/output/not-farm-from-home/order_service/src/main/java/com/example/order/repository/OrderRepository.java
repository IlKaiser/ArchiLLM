package com.example.order.repository;

import com.example.order.domain.Order;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface OrderRepository extends CrudRepository<Order, Long> {
    // Additional query methods can be defined here if needed
}