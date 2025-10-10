package com.socks.rating.domain;
public record Rating(String userId, String orderId, int rating, String review) {}
