package com.example.cart.controller;

import com.example.cart.query.CartReadModel;
import com.example.cart.query.CartReadService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/carts")
public class CartQueryController {

    private final CartReadService cartReadService;

    public CartQueryController(CartReadService cartReadService) {
        this.cartReadService = cartReadService;
    }

    @GetMapping("/{cartId}")
    public CartReadModel getCart(@PathVariable Long cartId) {
        return cartReadService.findCartById(cartId);
    }

    @GetMapping
    public List<CartReadModel> getAllCarts() {
        return cartReadService.findAllCarts();
    }
}