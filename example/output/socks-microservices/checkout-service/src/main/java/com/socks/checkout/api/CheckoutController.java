package com.socks.checkout.api;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
@RestController
@RequestMapping("/checkout")
public class CheckoutController {
    record Req(String userId, Map<String,Object> paymentInfo, Map<String,Object> shippingAddress) {}
    record Res(String result, String orderId) {}
    @PostMapping
    public Res checkout(@RequestBody Req req){
        String orderId = java.util.UUID.randomUUID().toString();
        return new Res("SUCCESS", orderId);
    }
}
