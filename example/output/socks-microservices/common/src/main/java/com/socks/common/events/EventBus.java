package com.socks.common.events;
import java.util.function.Consumer;
public interface EventBus {
    void publish(DomainEvent event);
    void subscribe(String type, Consumer<DomainEvent> handler);
}
