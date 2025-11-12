package com.example.order.saga;

import com.example.order.domain.Order;
import com.example.order.domain.OrderRepository;
import com.example.order.domain.OrderEvent;
import com.example.order.domain.OrderStatus;
import com.example.order.event.OrderCreatedEvent;
import com.example.order.event.OrderPaidEvent;
import com.example.order.event.OrderCancelledEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

// TODO: Integrate with Payment Service (e.g., via messaging or REST)

@Component
public class OrderSaga {

    private final OrderRepository orderRepository;

    @Autowired
    public OrderSaga(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    @Transactional
    public void handleOrderCreated(Long orderId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new IllegalArgumentException("Order not found: " + orderId));
        // TODO: Send payment request to Payment Service
        // For now, simulate payment success
        onPaymentCompleted(orderId);
    }

    @Transactional
    public void onPaymentCompleted(Long orderId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new IllegalArgumentException("Order not found: " + orderId));
        order.setStatus(OrderStatus.PAID);
        order.addDomainEvent(new OrderPaidEvent(orderId));
        orderRepository.save(order);
        // TODO: Publish OrderPaidEvent to event bus
    }

    @Transactional
    public void onPaymentFailed(Long orderId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new IllegalArgumentException("Order not found: " + orderId));
        order.setStatus(OrderStatus.CANCELLED);
        order.addDomainEvent(new OrderCancelledEvent(orderId));
        orderRepository.save(order);
        // TODO: Publish OrderCancelledEvent to event bus
    }
}