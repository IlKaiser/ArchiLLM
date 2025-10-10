package com.socks.cart.api;
import com.socks.cart.app.CartService;
import com.socks.cart.domain.Cart;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/cart/{userId}")
public class CartController {
    private final CartService svc;
    public CartController(CartService svc){ this.svc = svc; }
    @GetMapping
    public Cart get(@PathVariable String userId){ return svc.get(userId); }
    record ItemReq(String productId, Integer quantity) {}
    @PostMapping("/items")
    public ResponseEntity<Cart> add(@PathVariable String userId, @RequestBody ItemReq req){
        Cart c = svc.get(userId); c.add(req.productId(), req.quantity()); return ResponseEntity.ok(c);
    }
    @PutMapping("/items/{productId}")
    public ResponseEntity<Cart> update(@PathVariable String userId, @PathVariable String productId, @RequestBody ItemReq req){
        Cart c = svc.get(userId); c.update(productId, req.quantity()); return ResponseEntity.ok(c);
    }
    @DeleteMapping("/items/{productId}")
    public ResponseEntity<Cart> remove(@PathVariable String userId, @PathVariable String productId){
        Cart c = svc.get(userId); c.remove(productId); return ResponseEntity.ok(c);
    }
}
