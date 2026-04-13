package com.jwo.auth.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import lombok.extern.slf4j.Slf4j;
import lombok.RequiredArgsConstructor;
import com.jwo.auth.dto.AuthorizationRequest;
import com.jwo.auth.dto.AuthorizationResponse;
import com.jwo.auth.service.AuthorizationService;
import com.jwo.auth.service.ConfigurationService;
import com.jwo.auth.service.StoreConfiguration;
import java.util.UUID;

/**
 * REST Controller for authorization check endpoint
 */
@RestController
@Slf4j
@RequiredArgsConstructor
@RequestMapping("/v1")
public class AuthorizationController {

    private final AuthorizationService authorizationService;
    private final ConfigurationService configurationService;

    /**
     * POST /v1/authorize/check-entry
     * Check if customer can enter
     */
    @PostMapping("/authorize/check-entry")
    public ResponseEntity<AuthorizationResponse> checkEntry(@RequestBody AuthorizationRequest request) {
        log.info("Authorization request received: storeId={}, requestId={}", 
                 request.getStoreId(), request.getRequestId());

        try {
            // Validate request
            if (request.getStoreId() == null || request.getStoreId().trim().isEmpty()) {
                return ResponseEntity.badRequest()
                        .body(AuthorizationResponse.builder()
                                .decision(AuthorizationResponse.Decision.DENIED_INVALID_INPUT.value)
                                .reason("Store ID is required")
                                .timestamp(java.time.Instant.now().toString())
                                .build());
            }

            if (request.getCardData() == null || 
                request.getCardData().getCardNumber() == null ||
                request.getCardData().getCardNumber().trim().isEmpty()) {
                return ResponseEntity.badRequest()
                        .body(AuthorizationResponse.builder()
                                .decision(AuthorizationResponse.Decision.DENIED_INVALID_INPUT.value)
                                .reason("Card data is required")
                                .timestamp(java.time.Instant.now().toString())
                                .build());
            }

            // Generate request ID if not provided
            String requestId = request.getRequestId();
            if (requestId == null || requestId.trim().isEmpty()) {
                requestId = UUID.randomUUID().toString();
            }

            // Call authorization service
            AuthorizationResponse response = authorizationService.authorize(
                    request.getCardData().getCardNumber(),
                    request.getCardData().getCardNetwork() != null ? request.getCardData().getCardNetwork() : "UNKNOWN",
                    request.getStoreId(),
                    requestId
            );

            // Return 200 for all decisions (check decision field for result)
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("Exception during authorization", e);
            return ResponseEntity.status(500)
                    .body(AuthorizationResponse.builder()
                            .decision(AuthorizationResponse.Decision.DENIED_PROCESSOR_ERROR.value)
                            .reason("Internal server error")
                            .timestamp(java.time.Instant.now().toString())
                            .build());
        }
    }

    /**
     * GET /v1/config/store/{storeId}
     * Get store configuration
     */
    @GetMapping("/config/store/{storeId}")
    public ResponseEntity<StoreConfiguration> getConfig(@PathVariable String storeId) {
        log.info("Config request for store: {}", storeId);
        StoreConfiguration config = configurationService.getConfiguration(storeId);
        return ResponseEntity.ok(config);
    }

    /**
     * POST /v1/config/store/{storeId}
     * Set store configuration
     */
    @PostMapping("/config/store/{storeId}")
    public ResponseEntity<StoreConfiguration> setConfig(
            @PathVariable String storeId,
            @RequestBody StoreConfiguration config) {
        log.info("Setting config for store: {}", storeId);
        
        // Validate config
        if (config.getThresholdMultiplier() < 0.5 || config.getThresholdMultiplier() > 10.0) {
            return ResponseEntity.badRequest().build();
        }
        if (config.getAverageBasketSize() <= 0) {
            return ResponseEntity.badRequest().build();
        }

        config.setStoreId(storeId);
        configurationService.setConfiguration(storeId, config);
        return ResponseEntity.created(null).body(config);
    }

    /**
     * GET /v1/health
     * Health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<HealthResponse> health() {
        return ResponseEntity.ok(HealthResponse.builder()
                .status("UP")
                .timestamp(java.time.Instant.now().toString())
                .build());
    }

    @lombok.Data
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    @lombok.Builder
    public static class HealthResponse {
        private String status;
        private String timestamp;
    }
}
