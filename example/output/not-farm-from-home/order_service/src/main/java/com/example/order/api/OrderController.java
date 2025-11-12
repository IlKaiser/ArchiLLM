package com.example.order.api;

import com.example.order.domain.Order;
import com.example.order.domain.OrderService;
import com.example.order.domain.DeliveryInformation;
import com.example.order.domain.MenuItemIdAndQuantity;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;

import java.util.List;

// TODO: Add DTOs for request/response as needed for API composition

@RestController
@RequestMapping("/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody CreateOrderRequest request) {
        // TODO: Validate input, map DTOs as needed
        Order order = orderService.createOrder(
                request.getConsumerId(),
                request.getRestaurantId(),
                request.getDeliveryInformation(),
                request.getLineItems()
        );
        return new ResponseEntity<>(order, HttpStatus.CREATED);
    }

    @GetMapping("/{orderId}")
    public ResponseEntity<Order> getOrder(@PathVariable Long orderId) {
        // TODO: Implement find by id, handle not found
        Order order = orderService.findOrder(orderId);
        if (order == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(order);
    }

    // TODO: Add endpoints for cancel, revise, etc. as needed

    // --- DTOs for request/response ---

    public static class CreateOrderRequest {
        private Long consumerId;
        private Long restaurantId;
        private DeliveryInformation deliveryInformation;
        private List<MenuItemIdAndQuantity> lineItems;

        public Long getConsumerId() {
            return consumerId;
        }

        public void setConsumerId(Long consumerId) {
            this.consumerId = consumerId;
        }

        public Long getRestaurantId() {
            return restaurantId;
        }

        public void setRestaurantId(Long restaurantId) {
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