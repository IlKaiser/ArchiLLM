package com.socks.order.api;
import com.socks.order.domain.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
@RestController
@RequestMapping("/orders")
public class OrderController {
    private final Map<String, Order> orders = new ConcurrentHashMap<>();
    record CreateReq(String userId, List<OrderItem> orderItems, String shippingAddress, String paymentStatus) {}
    record CreateRes(String orderId, String confirmation) {}
    @PostMapping
    public CreateRes create(@RequestBody CreateReq req){
        String id = UUID.randomUUID().toString();
        orders.put(id, new Order(id, req.userId(), req.orderItems(), req.shippingAddress(), req.paymentStatus(), "CONFIRMED"));
        return new CreateRes(id, "ORDER_CONFIRMED");
    }
    @GetMapping("/{orderId}")
    public ResponseEntity<Order> get(@PathVariable String orderId){
        var o = orders.get(orderId);
        return o==null ? ResponseEntity.notFound().build() : ResponseEntity.ok(o);
    }
    @GetMapping("/user/{userId}")
    public List<Order> history(@PathVariable String userId){
        return orders.values().stream().filter(o -> o.userId().equals(userId)).toList();
    }
    @PostMapping("/{orderId}/reorder")
    public Map<String,String> reorder(@PathVariable String orderId){
        var old = orders.get(orderId);
        if(old==null) return Map.of("error","not found");
        String newId = UUID.randomUUID().toString();
        orders.put(newId, new Order(newId, old.userId(), old.items(), old.shippingAddress(), "PAID", "CONFIRMED"));
        return Map.of("newOrderId", newId);
    }
}
