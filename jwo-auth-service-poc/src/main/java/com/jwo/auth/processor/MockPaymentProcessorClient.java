package com.jwo.auth.processor;

import org.springframework.stereotype.Service;
import lombok.extern.slf4j.Slf4j;
import java.util.Random;

/**
 * Mock processor implementation for testing
 */
@Service
@Slf4j
public class MockPaymentProcessorClient implements PaymentProcessorClient {

    private final Random random = new Random();

    @Override
    public BalanceQueryResponse queryBalance(BalanceQueryRequest request) {
        try {
            log.info("MockProcessor: Querying balance for store: {}", request.getStoreId());
            
            // Simulate processor latency (50-300ms)
            Thread.sleep(50 + random.nextInt(250));

            // Mock balance: 60-75% of transaction amount + random variance
            long balance = (long) ((request.getTransactionAmountCents() + 5000) * (0.6 + random.nextDouble() * 0.15));
            
            return BalanceQueryResponse.builder()
                    .status("SUCCESS")
                    .availableBalanceCents(balance)
                    .preauthId("PREAUTH-" + System.currentTimeMillis())
                    .build();
        } catch (InterruptedException e) {
            log.error("MockProcessor: Thread interrupted during balance query", e);
            return BalanceQueryResponse.builder()
                    .status("ERROR")
                    .error("Interrupted")
                    .build();
        }
    }

    @Override
    public PreauthReverseResponse reversePreauth(PreauthReverseRequest request) {
        log.info("MockProcessor: Reversing preauth: {}", request.getPreauthId());
        
        // 95% success rate
        if (random.nextDouble() > 0.95) {
            return PreauthReverseResponse.builder()
                    .status("ERROR")
                    .error("Reversal failed")
                    .build();
        }

        return PreauthReverseResponse.builder()
                .status("SUCCESS")
                .voidedAmountCents(15000L)
                .build();
    }

    @Override
    public BINLookupResponse lookupBIN(String cardNumber) {
        log.info("MockProcessor: Looking up BIN for card: {}", maskCard(cardNumber));
        
        if (cardNumber == null || cardNumber.length() < 6) {
            return BINLookupResponse.builder()
                    .isPrepaid(false)
                    .cardType("UNKNOWN")
                    .network("UNKNOWN")
                    .build();
        }

        String bin = cardNumber.substring(0, 6);
        
        // Simple mock: return prepaid for specific BINs
        return BINLookupResponse.builder()
                .cardType("VISA")
                .network("VISA")
                .isPrepaid(bin.startsWith("411") || bin.startsWith("441")) // Common prepaid BINs
                .build();
    }

    private String maskCard(String cardNumber) {
        if (cardNumber == null || cardNumber.length() < 4) {
            return "****";
        }
        return "**** **** **** " + cardNumber.substring(cardNumber.length() - 4);
    }
}
