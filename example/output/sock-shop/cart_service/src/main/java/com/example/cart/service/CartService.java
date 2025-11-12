package com.example.cart.service;

import com.example.cart.model.Cart;
import com.example.cart.model.CartItem;
import com.example.cart.repository.CartRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.Optional;

@Service
public class CartService {
    @Autowired
    private CartRepository cartRepository;

    public Cart getCart(String userId) {
        return cartRepository.findById(userId).orElseGet(() -> {
            Cart cart = new Cart();
            cart.setUserId(userId);
            return cartRepository.save(cart);
        });
    }

    public Cart addItem(String userId, CartItem item) {
        Cart cart = getCart(userId);
        cart.getItems().add(item);
        return cartRepository.save(cart);
    }

    public Cart updateItem(String userId, Long productId, int quantity) {
        Cart cart = getCart(userId);
        cart.getItems().stream()
            .filter(i -> i.getProductId().equals(productId))
            .findFirst()
            .ifPresent(i -> i.setQuantity(quantity));
        return cartRepository.save(cart);
    }

    public Cart removeItem(String userId, Long productId) {
        Cart cart = getCart(userId);
        cart.getItems().removeIf(i -> i.getProductId().equals(productId));
        return cartRepository.save(cart);
    }
}