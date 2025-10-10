package com.socks.order.domain;
import java.util.List;
public record Order(String id, String userId, List<OrderItem> items, String shippingAddress, String paymentStatus, String status){}
