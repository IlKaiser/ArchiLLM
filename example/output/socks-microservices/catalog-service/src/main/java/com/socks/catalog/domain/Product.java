package com.socks.catalog.domain;
import java.math.BigDecimal;
public record Product(String id, String name, String description, BigDecimal price, int stock, String image){}
