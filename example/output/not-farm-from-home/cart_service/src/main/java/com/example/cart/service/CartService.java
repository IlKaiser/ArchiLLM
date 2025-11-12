package com.example.cart.service;

import com.example.cart.domain.Cart;
import com.example.cart.domain.CartEvent;
import com.example.cart.domain.CartRepository;
import com.example.cart.saga.OrderSaga;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
public class CartService {

    private final CartRepository cartRepository;
    private final ApplicationEventPublisher eventPublisher;
    private final OrderSaga orderSaga;

    public CartService(CartRepository cartRepository,
                       ApplicationEventPublisher eventPublisher,
                       OrderSaga orderSaga) {
        this.cartRepository = cartRepository;
        this.eventPublisher = eventPublisher;
        this.orderSaga = orderSaga;
    }

    @Transactional
    public Cart createCart(String userId) {
        Cart cart = new Cart(userId);
        cartRepository.save(cart);
        publishEvent(new CartEvent.CartCreatedEvent(cart.getId(), userId));
        return cart;
    }

    @Transactional
    public Optional<Cart> addItemToCart(Long cartId, String productId, int quantity) {
        Optional<Cart> cartOpt = cartRepository.findById(cartId);
        if (cartOpt.isPresent()) {
            Cart cart = cartOpt.get();
            cart.addItem(productId, quantity);
            cartRepository.save(cart);
            publishEvent(new CartEvent.ItemAddedEvent(cartId, productId, quantity));
            return Optional.of(cart);
        }
        return Optional.empty();
    }

    @Transactional
    public Optional<Cart> removeItemFromCart(Long cartId, String productId) {
        Optional<Cart> cartOpt = cartRepository.findById(cartId);
        if (cartOpt.isPresent()) {
            Cart cart = cartOpt.get();
            cart.removeItem(productId);
            cartRepository.save(cart);
            publishEvent(new CartEvent.ItemRemovedEvent(cartId, productId));
            return Optional.of(cart);
        }
        return Optional.empty();
    }

    @Transactional
    public Optional<Cart> checkout(Long cartId) {
        Optional<Cart> cartOpt = cartRepository.findById(cartId);
        if (cartOpt.isPresent()) {
            Cart cart = cartOpt.get();
            // Start Order Saga for checkout
            orderSaga.start(cart);
            publishEvent(new CartEvent.CheckedOutEvent(cartId));
            return Optional.of(cart);
        }
        return Optional.empty();
    }

    private void publishEvent(Object event) {
        // In a real implementation, this would publish to an event bus or outbox
        eventPublisher.publishEvent(event);
        // TODO: Integrate with external event system if needed
    }
}