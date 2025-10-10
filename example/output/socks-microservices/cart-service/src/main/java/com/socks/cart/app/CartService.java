package com.socks.cart.app;
import com.socks.cart.domain.Cart;
import org.springframework.stereotype.Service;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
@Service
public class CartService {
    private final Map<String, Cart> carts = new ConcurrentHashMap<>();
    public Cart get(String userId){ return carts.computeIfAbsent(userId, Cart::new); }
}
