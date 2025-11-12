package com.example.order.api;

import com.example.order.domain.Order;
import com.example.order.domain.OrderService;
import com.example.order.domain.DeliveryInformation;
import com.example.order.domain.MenuItemIdAndQuantity;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

// Minimal REST controller for order operations
@RestController
@RequestMapping("/orders")
public class OrderController {

    private final OrderService orderService;

    @Autowired
    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody CreateOrderRequest request) {
        // TODO: Validate input
        Order order = orderService.createOrder(
                request.getConsumerId(),
                request.getRestaurantId(),
                request.getDeliveryInformation(),
                request.getLineItems()
        );
        return ResponseEntity.ok(order);
    }

    // TODO: Add endpoints for get, cancel, revise, etc.

    // DTO for create order request
    public static class CreateOrderRequest {
        private long consumerId;
        private long restaurantId;
        private DeliveryInformation deliveryInformation;
        private List<MenuItemIdAndQuantity> lineItems;

        public long getConsumerId() {
            return consumerId;
        }

        public void setConsumerId(long consumerId) {
            this.consumerId = consumerId;
        }

        public long getRestaurantId() {
            return restaurantId;
        }

        public void setRestaurantId(long restaurantId) {
            this.restaurantId = restaurantId;
        }

        public DeliveryInformation getDeliveryInformation() {
            return deliveryInformation;
        }

        public void setDeliveryInformation(DeliveryInformation deliveryInformation) {
            this.deliveryInformation = deliveryInformation;
        }

        public List<MenuItemIdAndQuantity> getLineItems() {
            return lineItems;
        }

        public void setLineItems(List<MenuItemIdAndQuantity> lineItems) {
            this.lineItems = lineItems;
        }
    }
}