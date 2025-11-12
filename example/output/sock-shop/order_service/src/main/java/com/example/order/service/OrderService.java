package com.example.order.service;

import com.example.order.domain.Order;
import com.example.order.domain.OrderRepository;
import com.example.order.domain.Restaurant;
import com.example.order.domain.RestaurantRepository;
import com.example.order.domain.DeliveryInformation;
import com.example.order.domain.MenuItem;
import com.example.order.domain.MenuItemIdAndQuantity;
import com.example.order.domain.OrderLineItem;
import com.example.order.domain.OrderDomainEvent;
import com.example.order.domain.OrderDetails;
import com.example.order.domain.OrderDomainEventPublisher;
import com.example.order.saga.CreateOrderSaga;
import com.example.order.saga.CreateOrderSagaState;
import com.example.order.saga.CancelOrderSaga;
import com.example.order.saga.ReviseOrderSaga;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

// TODO: Integrate with actual event publisher and saga instance factory
public class OrderService {

    private final Logger logger = LoggerFactory.getLogger(getClass());

    // TODO: Replace Object with actual SagaInstanceFactory type
    private final Object sagaInstanceFactory;

    private final OrderRepository orderRepository;
    private final RestaurantRepository restaurantRepository;
    private final CreateOrderSaga createOrderSaga;
    private final CancelOrderSaga cancelOrderSaga;
    private final ReviseOrderSaga reviseOrderSaga;
    private final OrderDomainEventPublisher orderAggregateEventPublisher;
    private final Optional<Object> meterRegistry; // TODO: Replace Object with actual MeterRegistry type

    public OrderService(
            Object sagaInstanceFactory,
            OrderRepository orderRepository,
            RestaurantRepository restaurantRepository,
            CreateOrderSaga createOrderSaga,
            CancelOrderSaga cancelOrderSaga,
            ReviseOrderSaga reviseOrderSaga,
            OrderDomainEventPublisher orderAggregateEventPublisher,
            Optional<Object> meterRegistry // TODO: Replace Object with actual MeterRegistry type
    ) {
        this.sagaInstanceFactory = sagaInstanceFactory;
        this.orderRepository = orderRepository;
        this.restaurantRepository = restaurantRepository;
        this.createOrderSaga = createOrderSaga;
        this.cancelOrderSaga = cancelOrderSaga;
        this.reviseOrderSaga = reviseOrderSaga;
        this.orderAggregateEventPublisher = orderAggregateEventPublisher;
        this.meterRegistry = meterRegistry;
    }

    @Transactional
    public Order createOrder(
            long consumerId,
            long restaurantId,
            DeliveryInformation deliveryInformation,
            List<MenuItemIdAndQuantity> lineItems
    ) {
        Restaurant restaurant = restaurantRepository.findById(restaurantId)
                .orElseThrow(() -> new RuntimeException("Restaurant not found: " + restaurantId));

        List<OrderLineItem> orderLineItems = makeOrderLineItems(lineItems, restaurant);

        // TODO: Replace with actual ResultWithDomainEvents pattern if available
        Order order = Order.createOrder(consumerId, restaurant, deliveryInformation, orderLineItems);
        orderRepository.save(order);

        // TODO: Publish domain events
        orderAggregateEventPublisher.publish(order, order.getDomainEvents());

        OrderDetails orderDetails = new OrderDetails(consumerId, restaurantId, orderLineItems, order.getOrderTotal());

        CreateOrderSagaState data = new CreateOrderSagaState(order.getId(), orderDetails);
        // TODO: Start saga using sagaInstanceFactory
        // sagaInstanceFactory.create(createOrderSaga, data);

        meterRegistry.ifPresent(mr -> {
            // TODO: Increment placed_orders counter
        });

        return order;
    }

    private List<OrderLineItem> makeOrderLineItems(List<MenuItemIdAndQuantity> lineItems, Restaurant restaurant) {
        return lineItems.stream().map(li -> {
            MenuItem menuItem = restaurant.findMenuItem(li.getMenuItemId())
                    .orElseThrow(() -> new RuntimeException("Invalid menu item id: " + li.getMenuItemId()));
            return new OrderLineItem(li.getMenuItemId(), menuItem.getName(), menuItem.getPrice(), li.getQuantity());
        }).collect(Collectors.toList());
    }

    // TODO: Implement other order-related business operations (cancel, revise, etc.) and sagas

}