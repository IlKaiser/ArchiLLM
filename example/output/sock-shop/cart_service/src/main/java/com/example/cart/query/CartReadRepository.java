package com.example.cart.query;

import com.example.cart.query.model.CartReadModel;
import java.util.List;
import java.util.Optional;

public interface CartReadRepository {

    Optional<CartReadModel> findById(Long cartId);

    List<CartReadModel> findAll();

    // TODO: Add more query methods as needed for CQRS read side

}