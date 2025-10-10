package com.socks.common.events;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Consumer;
public class InMemoryEventBus implements EventBus {
    private final Map<String, List<Consumer<DomainEvent>>> subs = new ConcurrentHashMap<>();
    @Override public void publish(DomainEvent event) {
        subs.getOrDefault(event.type(), List.of()).forEach(h -> h.accept(event));
        subs.getOrDefault("*", List.of()).forEach(h -> h.accept(event));
    }
    @Override public void subscribe(String type, Consumer<DomainEvent> handler) {
        subs.computeIfAbsent(type, k -> new ArrayList<>()).add(handler);
    }
}
