package com.example.cart.service;

import com.example.cart.domain.Cart;
import com.example.cart.domain.CartItem;
import com.example.cart.repository.CartRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
public class CartCommandService {

    private final CartRepository cartRepository;

    public CartCommandService(CartRepository cartRepository) {
        this.cartRepository = cartRepository;
    }

    @Transactional
    public Cart createCart(String cartId) {
        Cart cart = new Cart(cartId);
        return cartRepository.save(cart);
    }

    @Transactional
    public Cart addItemToCart(String cartId, String productId, int quantity) {
        Cart cart = getOrCreateCart(cartId);
        cart.addItem(new CartItem(productId, quantity));
        return cartRepository.save(cart);
    }

    @Transactional
    public Cart removeItemFromCart(String cartId, String productId) {
        Cart cart = getOrCreateCart(cartId);
        cart.removeItem(productId);
        return cartRepository.save(cart);
    }

    @Transactional
    public Cart clearCart(String cartId) {
        Cart cart = getOrCreateCart(cartId);
        cart.clearItems();
        return cartRepository.save(cart);
    }

    private Cart getOrCreateCart(String cartId) {
        Optional<Cart> optionalCart = cartRepository.findById(cartId);
        return optionalCart.orElseGet(() -> new Cart(cartId));
    }

    // TODO: Integrate with Order Service to place order from cart
    // TODO: Publish domain events if needed
}