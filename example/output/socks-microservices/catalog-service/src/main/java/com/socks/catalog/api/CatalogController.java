package com.socks.catalog.api;
import com.socks.catalog.app.CatalogService;
import com.socks.catalog.domain.Product;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;
import java.util.List;
@RestController
@RequestMapping("/products")
public class CatalogController {
    private final CatalogService svc;
    public CatalogController(CatalogService svc){ this.svc = svc; }
    @GetMapping public List<Product> list(){ return svc.list(); }
    @GetMapping("/{productId}")
    public ResponseEntity<Product> get(@PathVariable String productId){
        return svc.get(productId).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }
    record UpsertReq(String name, String description, java.math.BigDecimal price, Integer stock, String image){}
    @PostMapping
    public ResponseEntity<Product> create(@RequestBody UpsertReq req){
        var p = svc.create(req.name(), req.description(), req.price(), req.stock(), req.image());
        return ResponseEntity.ok(p);
    }
    @PutMapping("/{productId}")
    public ResponseEntity<Product> update(@PathVariable String productId, @RequestBody UpsertReq req){
        return svc.update(productId, req.name(), req.description(), req.price(), req.stock(), req.image())
                  .map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }
}
