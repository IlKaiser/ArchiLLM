package com.socks.rating.api;
import com.socks.rating.domain.Rating;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
@RestController
@RequestMapping("/ratings")
public class RatingController {
    private final Map<String, List<Rating>> byOrder = new ConcurrentHashMap<>();
    record CreateReq(String userId, String orderId, Integer rating, String review) {}
    @PostMapping
    public Map<String, String> create(@RequestBody CreateReq req){
        var r = new Rating(req.userId(), req.orderId(), Math.max(1, Math.min(5, req.rating())), req.review());
        byOrder.computeIfAbsent(req.orderId(), k -> new ArrayList<>()).add(r);
        return Map.of("result", "OK");
    }
    @GetMapping("/{orderId}")
    public List<Rating> get(@PathVariable String orderId){
        return byOrder.getOrDefault(orderId, List.of());
    }
}
