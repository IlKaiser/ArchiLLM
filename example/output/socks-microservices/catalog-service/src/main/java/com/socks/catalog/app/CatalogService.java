package com.socks.catalog.app;
import com.socks.catalog.domain.*;
import com.socks.common.events.EventBus;
import org.springframework.stereotype.Service;
import java.math.BigDecimal;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
@Service
public class CatalogService {
    private final Map<String, Product> store = new ConcurrentHashMap<>();
    private final EventBus bus;
    public CatalogService(EventBus bus){ this.bus = bus; seed(); }
    public List<Product> list(){ return new ArrayList<>(store.values()); }
    public Optional<Product> get(String id){ return Optional.ofNullable(store.get(id)); }
    public Product create(String name, String description, BigDecimal price, int stock, String image){
        String id = UUID.randomUUID().toString();
        Product p = new Product(id, name, description, price, Math.max(0, stock), image);
        store.put(id, p);
        bus.publish(new ProductCreated(id, java.time.Instant.now()));
        return p;
    }
    public Optional<Product> update(String id, String name, String description, BigDecimal price, int stock, String image){
        if(!store.containsKey(id)) return Optional.empty();
        Product p = new Product(id, name, description, price, Math.max(0, stock), image);
        store.put(id, p);
        bus.publish(new ProductUpdated(id, java.time.Instant.now()));
        return Optional.of(p);
    }
    private void seed(){
        create("Classic Crew","Comfy crew socks", new BigDecimal("7.99"), 42,"/img/crew.png");
        create("Ankle Runner","Breathable ankle socks", new BigDecimal("5.49"), 25,"/img/ankle.png");
    }
}
