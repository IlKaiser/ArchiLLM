package com.socks.monitoring.api;
import org.springframework.web.bind.annotation.*;
import java.util.*;
@RestController
public class MonitoringController {
    @GetMapping("/metrics")
    public Map<String,Object> metrics(){
        return Map.of("uptimeSeconds", System.currentTimeMillis()/1000,
                      "heapUsedBytes", Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory(),
                      "status","UP");
    }
    @GetMapping("/alerts")
    public List<Map<String,String>> alerts(){
        return List.of();
    }
}
