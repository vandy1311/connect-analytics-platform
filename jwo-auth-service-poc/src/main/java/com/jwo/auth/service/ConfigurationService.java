package com.jwo.auth.service;

import org.springframework.stereotype.Service;
import lombok.extern.slf4j.Slf4j;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;

/**
 * Service for managing store configurations with in-memory caching
 */
@Service
@Slf4j
public class ConfigurationService {

    private final ConcurrentHashMap<String, StoreConfiguration> configStore = new ConcurrentHashMap<>();
    
    // Simple cache (replacing Caffeine for minimal deps)
    private final CacheSimple<String, StoreConfiguration> cache = new CacheSimple<>(5 * 60 * 1000); // 5 min TTL

    /**
     * Get store configuration (from cache if available, else from store)
     */
    public StoreConfiguration getConfiguration(String storeId) {
        long startTime = System.currentTimeMillis();
        
        // Check cache first
        StoreConfiguration cached = cache.get(storeId);
        if (cached != null) {
            log.debug("Config cache hit for store: {}", storeId);
            return cached;
        }

        // Check store
        StoreConfiguration config = configStore.get(storeId);
        if (config == null) {
            log.debug("Config not found for store: {}, using defaults", storeId);
            config = StoreConfiguration.builder()
                    .storeId(storeId)
                    .thresholdMultiplier(3.0)
                    .averageBasketSize(50.0)
                    .build();
        } else {
            log.debug("Config loaded from store for store: {}", storeId);
        }

        // Cache the config
        cache.put(storeId, config);
        
        long elapsed = System.currentTimeMillis() - startTime;
        log.debug("Config retrieval took {}ms for store: {}", elapsed, storeId);
        
        return config;
    }

    /**
     * Set store configuration
     */
    public void setConfiguration(String storeId, StoreConfiguration config) {
        log.info("Setting configuration for store: {}", storeId);
        configStore.put(storeId, config);
        cache.invalidate(storeId); // invalidate cache
    }

    /**
     * Simple in-memory cache implementation
     */
    private static class CacheSimple<K, V> {
        private final ConcurrentHashMap<K, CacheEntry<V>> cache = new ConcurrentHashMap<>();
        private final long ttlMs;

        CacheSimple(long ttlMs) {
            this.ttlMs = ttlMs;
        }

        void put(K key, V value) {
            cache.put(key, new CacheEntry<>(value, System.currentTimeMillis()));
        }

        V get(K key) {
            CacheEntry<V> entry = cache.get(key);
            if (entry == null) return null;
            
            if (System.currentTimeMillis() - entry.timestamp > ttlMs) {
                cache.remove(key);
                return null;
            }
            return entry.value;
        }

        void invalidate(K key) {
            cache.remove(key);
        }

        private static class CacheEntry<V> {
            final V value;
            final long timestamp;

            CacheEntry(V value, long timestamp) {
                this.value = value;
                this.timestamp = timestamp;
            }
        }
    }
}
