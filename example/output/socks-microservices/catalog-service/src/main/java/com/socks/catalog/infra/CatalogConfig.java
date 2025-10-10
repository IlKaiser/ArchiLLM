package com.socks.catalog.infra;
import com.socks.common.events.EventBus;
import com.socks.common.events.InMemoryEventBus;
import org.springframework.context.annotation.Bean; import org.springframework.context.annotation.Configuration;
@Configuration
public class CatalogConfig {
    @Bean EventBus eventBus(){ return new InMemoryEventBus(); }
}
