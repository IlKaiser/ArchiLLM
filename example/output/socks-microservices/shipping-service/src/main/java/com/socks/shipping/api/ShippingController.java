package com.socks.shipping.api;
import com.socks.shipping.domain.Shipment;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
@RestController
@RequestMapping("/shipments")
public class ShippingController {
    private final Map<String, Shipment> shipments = new ConcurrentHashMap<>();
    record CreateReq(String orderId, String shippingAddress) {}
    @PostMapping
    public Shipment create(@RequestBody CreateReq req){
        var s = new Shipment(req.orderId(), req.shippingAddress(), "CREATED");
        shipments.put(req.orderId(), s);
        return s;
    }
    @GetMapping("/{orderId}")
    public ResponseEntity<Shipment> get(@PathVariable String orderId){
        var s = shipments.get(orderId);
        return s==null ? ResponseEntity.notFound().build() : ResponseEntity.ok(s);
    }
    record UpdateReq(String status) {}
    @PutMapping("/{orderId}/update")
    public ResponseEntity<Shipment> update(@PathVariable String orderId, @RequestBody UpdateReq req){
        var s = shipments.get(orderId);
        if(s==null) return ResponseEntity.notFound().build();
        var updated = new Shipment(s.orderId(), s.address(), req.status());
        shipments.put(orderId, updated);
        return ResponseEntity.ok(updated);
    }
}
