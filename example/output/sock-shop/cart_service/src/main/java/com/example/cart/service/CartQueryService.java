package com.example.cart.service;

import com.example.cart.domain.Cart;
import com.example.cart.domain.CartItem;
import com.example.cart.repository.CartReadRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class CartQueryService {

    private final CartReadRepository cartReadRepository;

    public CartQueryService(CartReadRepository cartReadRepository) {
        this.cartReadRepository = cartReadRepository;
    }

    public Optional<Cart> findCartById(Long cartId) {
        return cartReadRepository.findById(cartId);
    }

    public List<CartItem> findCartItems(Long cartId) {
        return cartReadRepository.findItemsByCartId(cartId);
    }

    // TODO: Add more query methods as needed for CQRS read side
}