package com.socks.logging.api;
import com.socks.logging.domain.LogEntry;
import org.springframework.web.bind.annotation.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
@RestController
@RequestMapping("/logs")
public class LoggingController {
    private final Map<String, LogEntry> logs = new ConcurrentHashMap<>();
    record CreateReq(String eventType, String eventData, Instant timestamp) {}
    @PostMapping
    public Map<String,String> create(@RequestBody CreateReq req){
        String id = UUID.randomUUID().toString();
        logs.put(id, new LogEntry(id, req.eventType(), req.eventData(), req.timestamp()==null? Instant.now(): req.timestamp()));
        return Map.of("logId", id);
    }
    @GetMapping
    public List<LogEntry> get(@RequestParam(required=false) String filter,
                              @RequestParam(required=false) String dateRange){
        return new ArrayList<>(logs.values());
    }
}
