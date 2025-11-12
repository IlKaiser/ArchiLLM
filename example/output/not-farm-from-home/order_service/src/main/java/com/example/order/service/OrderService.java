package com.example.order.service;

import com.example.order.domain.Order;
import com.example.order.domain.OrderRepository;
import com.example.order.domain.Restaurant;
import com.example.order.domain.RestaurantRepository;
import com.example.order.domain.OrderDomainEventPublisher;
import com.example.order.domain.DeliveryInformation;
import com.example.order.domain.OrderLineItem;
import com.example.order.domain.MenuItemIdAndQuantity;
import com.example.order.domain.OrderDomainEvent;
import com.example.order.saga.CreateOrderSaga;
import com.example.order.saga.CancelOrderSaga;
import com.example.order.saga.ReviseOrderSaga;
import com.example.order.saga.CreateOrderSagaState;
import com.example.order.exception.RestaurantNotFoundException;
import com.example.order.exception.InvalidMenuItemIdException;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

// TODO: Integrate with event publishing infrastructure
// TODO: Integrate with saga orchestration infrastructure
// TODO: Integrate with metrics/monitoring if needed

@Service
public class OrderService {

    private final OrderRepository orderRepository;
    private final RestaurantRepository restaurantRepository;
    private final CreateOrderSaga createOrderSaga;
    private final CancelOrderSaga cancelOrderSaga;
    private final ReviseOrderSaga reviseOrderSaga;
    private final OrderDomainEventPublisher orderAggregateEventPublisher;
    // TODO: Inject saga instance factory and event publisher as needed

    public OrderService(OrderRepository orderRepository,
                       RestaurantRepository restaurantRepository,
                       CreateOrderSaga createOrderSaga,
                       CancelOrderSaga cancelOrderSaga,
                       ReviseOrderSaga reviseOrderSaga,
                       OrderDomainEventPublisher orderAggregateEventPublisher) {
        this.orderRepository = orderRepository;
        this.restaurantRepository = restaurantRepository;
        this.createOrderSaga = createOrderSaga;
        this.cancelOrderSaga = cancelOrderSaga;
        this.reviseOrderSaga = reviseOrderSaga;
        this.orderAggregateEventPublisher = orderAggregateEventPublisher;
    }

    @Transactional
    public Order createOrder(long consumerId, long restaurantId, DeliveryInformation deliveryInformation,
                             List<MenuItemIdAndQuantity> lineItems) {
        Restaurant restaurant = restaurantRepository.findById(restaurantId)
                .orElseThrow(() -> new RestaurantNotFoundException(restaurantId));

        List<OrderLineItem> orderLineItems = makeOrderLineItems(lineItems, restaurant);

        // Aggregate creation and domain events
        Order order = Order.createOrder(consumerId, restaurant, deliveryInformation, orderLineItems);
        orderRepository.save(order);

        // TODO: Publish domain events
        orderAggregateEventPublisher.publish(order, order.getDomainEvents());

        // TODO: Start saga for order creation
        CreateOrderSagaState sagaState = new CreateOrderSagaState(order.getId(), consumerId, restaurantId, orderLineItems, order.getOrderTotal());
        // sagaInstanceFactory.create(createOrderSaga, sagaState);

        return order;
    }

    private List<OrderLineItem> makeOrderLineItems(List<MenuItemIdAndQuantity> lineItems, Restaurant restaurant) {
        return lineItems.stream().map(li -> {
            return restaurant.findMenuItem(li.getMenuItemId())
                    .map(menuItem -> new OrderLineItem(li.getMenuItemId(), menuItem.getName(), menuItem.getPrice(), li.getQuantity()))
                    .orElseThrow(() -> new InvalidMenuItemIdException(li.getMenuItemId()));
        }).collect(Collectors.toList());
    }

    // TODO: Implement cancelOrder, reviseOrder, and other business operations as needed
}