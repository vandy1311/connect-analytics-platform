package com.jwo.auth.service;

import org.springframework.stereotype.Service;
import lombok.extern.slf4j.Slf4j;
import lombok.RequiredArgsConstructor;
import com.jwo.auth.dto.AuthorizationResponse;
import com.jwo.auth.processor.*;
import java.time.Instant;
import java.util.concurrent.TimeUnit;

/**
 * Core Authorization Service
 * Handles the authorization decision logic
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class AuthorizationService {

    private final ConfigurationService configService;
    private final PaymentProcessorClient processorClient;
    private final EventLogger eventLogger;

    private static final long REQUEST_TIMEOUT_MS = 1200;
    private static final long BALANCE_QUERY_TIMEOUT_MS = 600;
    private static final long BIN_LOOKUP_TIMEOUT_MS = 200;

    /**
     * Main authorization method
     */
    public AuthorizationResponse authorize(String cardNumber, String cardNetwork, String storeId, String requestId) {
        long startTime = System.currentTimeMillis();
        String decision = null;
        String reason = null;
        Long availableBalance = null;
        Long requiredBalance = null;

        try {
            // 1. BIN Lookup - determine if prepaid
            BINLookupResponse binLookup = processorClient.lookupBIN(cardNumber);
            if (!binLookup.isPrepaid()) {
                decision = AuthorizationResponse.Decision.DENIED_NOT_PREPAID.value;
                reason = "Only prepaid cards are accepted";
                log.warn("Authorization denied: not prepaid card for store: {}, request: {}", storeId, requestId);
                return buildResponse(decision, null, null, startTime, reason, requestId);
            }

            // 2. Get store configuration
            StoreConfiguration config = configService.getConfiguration(storeId);
            log.debug("Config loaded for store: {}, multiplier: {}, basket: {}", 
                     storeId, config.getThresholdMultiplier(), config.getAverageBasketSize());

            // 3. Query balance from processor
            long requiredAmountCents = (long) (config.getThresholdMultiplier() * config.getAverageBasketSize() * 100);
            BalanceQueryRequest balanceRequest = BalanceQueryRequest.builder()
                    .cardToken("token-" + cardNumber.substring(cardNumber.length() - 4))
                    .transactionAmountCents(requiredAmountCents)
                    .storeId(storeId)
                    .build();

            BalanceQueryResponse balanceResponse = processorClient.queryBalance(balanceRequest);
            
            if (!balanceResponse.isSuccess() || balanceResponse.getAvailableBalanceCents() == null) {
                decision = AuthorizationResponse.Decision.DENIED_PROCESSOR_ERROR.value;
                reason = "Processor error: " + balanceResponse.getError();
                log.error("Authorization denied: processor error for store: {}, error: {}", 
                         storeId, balanceResponse.getError());
                return buildResponse(decision, null, requiredAmountCents, startTime, reason, requestId);
            }

            availableBalance = balanceResponse.getAvailableBalanceCents();
            requiredBalance = requiredAmountCents;

            // 4. Decision logic
            if (availableBalance >= requiredAmountCents) {
                decision = AuthorizationResponse.Decision.APPROVED.value;
                reason = "Approved";
                log.info("Authorization approved for store: {}, request: {}", storeId, requestId);
            } else {
                decision = AuthorizationResponse.Decision.DENIED_INSUFFICIENT_BALANCE.value;
                reason = String.format("Insufficient balance: %d < %d", availableBalance, requiredAmountCents);
                
                // Initiate reversal asynchronously
                if (balanceResponse.getPreauthId() != null) {
                    initiateReversalAsync(balanceResponse.getPreauthId());
                }
                
                log.warn("Authorization denied: insufficient balance for store: {}, available: {}, required: {}", 
                        storeId, availableBalance, requiredAmountCents);
            }

        } catch (Exception e) {
            decision = AuthorizationResponse.Decision.DENIED_PROCESSOR_ERROR.value;
            reason = "Unexpected error: " + e.getMessage();
            log.error("Authorization error for store: {}, request: {}", storeId, requestId, e);
        }

        return buildResponse(decision, availableBalance, requiredBalance, startTime, reason, requestId);
    }

    private AuthorizationResponse buildResponse(String decision, Long availableBalance, Long requiredBalance, 
                                               long startTime, String reason, String requestId) {
        long elapsed = System.currentTimeMillis() - startTime;
        
        AuthorizationResponse response = AuthorizationResponse.builder()
                .decision(decision)
                .availableBalanceCents(availableBalance)
                .requiredBalanceCents(requiredBalance)
                .totalDecisionTimeMs(elapsed)
                .reason(reason)
                .requestId(requestId)
                .timestamp(Instant.now().toString())
                .build();

        // Log the decision
        eventLogger.logAuthorizationEvent(response);

        return response;
    }

    private void initiateReversalAsync(String preauthId) {
        new Thread(() -> {
            try {
                log.debug("Initiating preauth reversal for preauthId: {}", preauthId);
                PreauthReverseRequest reverseRequest = PreauthReverseRequest.builder()
                        .preauthId(preauthId)
                        .build();
                PreauthReverseResponse reverseResponse = processorClient.reversePreauth(reverseRequest);
                
                if (reverseResponse.isSuccess()) {
                    log.info("Preauth reversal successful for preauthId: {}", preauthId);
                } else {
                    log.error("Preauth reversal failed for preauthId: {}, error: {}", preauthId, reverseResponse.getError());
                }
            } catch (Exception e) {
                log.error("Exception during preauth reversal for preauthId: {}", preauthId, e);
            }
        }).start();
    }
}
