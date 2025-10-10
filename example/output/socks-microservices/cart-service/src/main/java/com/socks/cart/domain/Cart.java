package com.socks.cart.domain;
import java.util.*;
public class Cart {
    private final String userId;
    private final Map<String, CartItem> items = new LinkedHashMap<>();
    public Cart(String userId){ this.userId = userId; }
    public String userId(){ return userId; }
    public Collection<CartItem> items(){ return items.values(); }
    public void add(String productId, int qty){
        if(qty <= 0) return;
        items.merge(productId, new CartItem(productId, qty),
            (oldv, newv) -> new CartItem(productId, Math.min(999, oldv.quantity()+newv.quantity())));
    }
    public void update(String productId, int qty){
        if(qty <= 0) items.remove(productId);
        else items.put(productId, new CartItem(productId, Math.min(999, qty)));
    }
    public void remove(String productId){ items.remove(productId); }
}
