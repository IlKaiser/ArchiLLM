package com.example.cart.repository;

import com.example.cart.domain.Cart;
import java.util.Optional;

public interface CartRepository {
    Cart save(Cart cart);

    Optional<Cart> findById(Long id);

    // TODO: Implement persistence integration
}