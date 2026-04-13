package com.jwo.auth.service;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Configuration model for a store
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StoreConfiguration {
    private String storeId;
    private double thresholdMultiplier;
    private double averageBasketSize;

    public StoreConfiguration withDefaults() {
        if (this.thresholdMultiplier <= 0) {
            this.thresholdMultiplier = 3.0; // Default 3x multiplier
        }
        if (this.averageBasketSize <= 0) {
            this.averageBasketSize = 50.0; // Default $50 basket
        }
        return this;
    }
}
