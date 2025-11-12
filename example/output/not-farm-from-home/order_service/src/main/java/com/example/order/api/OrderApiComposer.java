package com.example.order.api;

import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.Map;
import java.util.HashMap;

/**
 * Component for API composition, aggregating data from multiple services.
 */
@Component
public class OrderApiComposer {

    private final RestTemplate restTemplate;

    @Autowired
    public OrderApiComposer(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Compose order details by aggregating data from Order, Consumer, and Restaurant services.
     * This is a stub implementation. Replace URLs and response handling as needed.
     */
    public Map<String, Object> getComposedOrder(long orderId) {
        Map<String, Object> composed = new HashMap<>();

        // TODO: Replace with actual service URLs and response types
        String orderServiceUrl = "http://order-service/orders/" + orderId;
        String consumerServiceUrl = "http://consumer-service/consumers/";
        String restaurantServiceUrl = "http://restaurant-service/restaurants/";

        // Fetch order aggregate
        Map order = restTemplate.getForObject(orderServiceUrl, Map.class);
        composed.put("order", order);

        if (order != null) {
            // Fetch consumer details
            Object consumerId = order.get("consumerId");
            if (consumerId != null) {
                // TODO: Handle errors and response mapping
                Map consumer = restTemplate.getForObject(consumerServiceUrl + consumerId, Map.class);
                composed.put("consumer", consumer);
            }

            // Fetch restaurant details
            Object restaurantId = order.get("restaurantId");
            if (restaurantId != null) {
                // TODO: Handle errors and response mapping
                Map restaurant = restTemplate.getForObject(restaurantServiceUrl + restaurantId, Map.class);
                composed.put("restaurant", restaurant);
            }
        }

        // TODO: Compose additional data as needed

        return composed;
    }
}