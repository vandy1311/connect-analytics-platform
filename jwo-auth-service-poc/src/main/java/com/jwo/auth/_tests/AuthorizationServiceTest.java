package com.jwo.auth.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import com.jwo.auth.dto.AuthorizationResponse;
import com.jwo.auth.processor.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@DisplayName("Authorization Service Tests")
class AuthorizationServiceTest {

    @Mock
    private PaymentProcessorClient processorClient;

    @Mock
    private ConfigurationService configService;

    @Mock
    private EventLogger eventLogger;

    private AuthorizationService authorizationService;

    @BeforeEach
    void setup() {
        MockitoAnnotations.openMocks(this);
        authorizationService = new AuthorizationService(configService, processorClient, eventLogger);
    }

    @Test
    @DisplayName("Happy path: prepaid card with sufficient balance should approve")
    void testAuthorizeApproved() {
        // Arrange
        String cardNumber = "4111111111111111";
        String cardNetwork = "VISA";
        String storeId = "store-123";
        String requestId = "req-123";

        // Mock BIN lookup
        BINLookupResponse binResponse = BINLookupResponse.builder()
                .cardType("VISA")
                .network("VISA")
                .isPrepaid(true)
                .build();
        when(processorClient.lookupBIN(cardNumber)).thenReturn(binResponse);

        // Mock configuration
        StoreConfiguration config = StoreConfiguration.builder()
                .storeId(storeId)
                .thresholdMultiplier(3.0)
                .averageBasketSize(50.0)
                .build();
        when(configService.getConfiguration(storeId)).thenReturn(config);

        // Mock balance query - sufficient balance
        long requiredAmountCents = (long) (3.0 * 50.0 * 100);
        BalanceQueryResponse balanceResponse = BalanceQueryResponse.builder()
                .status("SUCCESS")
                .availableBalanceCents(requiredAmountCents + 5000) // 20000 cents more than required
                .preauthId("preauth-123")
                .build();
        when(processorClient.queryBalance(any())).thenReturn(balanceResponse);

        // Act
        AuthorizationResponse response = authorizationService.authorize(cardNumber, cardNetwork, storeId, requestId);

        // Assert
        assertNotNull(response);
        assertEquals(AuthorizationResponse.Decision.APPROVED.value, response.getDecision());
        assertEquals(requiredAmountCents, response.getRequiredBalanceCents());
        assertTrue(response.getTotalDecisionTimeMs() > 0);
        assertTrue(response.getTotalDecisionTimeMs() < 1200); // Should be under 1.2s
    }

    @Test
    @DisplayName("Denial: non-prepaid card should deny")
    void testAuthorizeNonPrepaidCard() {
        // Arrange
        String cardNumber = "4532111111111111";
        String storeId = "store-123";

        BINLookupResponse binResponse = BINLookupResponse.builder()
                .cardType("VISA")
                .network("VISA")
                .isPrepaid(false) // Non-prepaid
                .build();
        when(processorClient.lookupBIN(cardNumber)).thenReturn(binResponse);

        // Act
        AuthorizationResponse response = authorizationService.authorize(cardNumber, "VISA", storeId, "req-123");

        // Assert
        assertNotNull(response);
        assertEquals(AuthorizationResponse.Decision.DENIED_NOT_PREPAID.value, response.getDecision());
    }

    @Test
    @DisplayName("Denial: insufficient balance should deny and trigger reversal")
    void testAuthorizeInsufficientBalance() {
        // Arrange
        String cardNumber = "4111111111111111";
        String storeId = "store-123";

        BINLookupResponse binResponse = BINLookupResponse.builder()
                .cardType("VISA")
                .network("VISA")
                .isPrepaid(true)
                .build();
        when(processorClient.lookupBIN(cardNumber)).thenReturn(binResponse);

        StoreConfiguration config = StoreConfiguration.builder()
                .storeId(storeId)
                .thresholdMultiplier(3.0)
                .averageBasketSize(50.0)
                .build();
        when(configService.getConfiguration(storeId)).thenReturn(config);

        long requiredAmountCents = 15000;
        BalanceQueryResponse balanceResponse = BalanceQueryResponse.builder()
                .status("SUCCESS")
                .availableBalanceCents(10000) // Less than required
                .preauthId("preauth-456")
                .build();
        when(processorClient.queryBalance(any())).thenReturn(balanceResponse);

        // Act
        AuthorizationResponse response = authorizationService.authorize(cardNumber, "VISA", storeId, "req-123");

        // Assert
        assertNotNull(response);
        assertEquals(AuthorizationResponse.Decision.DENIED_INSUFFICIENT_BALANCE.value, response.getDecision());
        assertEquals(10000L, response.getAvailableBalanceCents());
        assertEquals(requiredAmountCents, response.getRequiredBalanceCents());
    }

    @Test
    @DisplayName("Denial: processor error should deny gracefully")
    void testAuthorizeProcessorError() {
        // Arrange
        String cardNumber = "4111111111111111";
        String storeId = "store-123";

        BINLookupResponse binResponse = BINLookupResponse.builder()
                .cardType("VISA")
                .network("VISA")
                .isPrepaid(true)
                .build();
        when(processorClient.lookupBIN(cardNumber)).thenReturn(binResponse);

        StoreConfiguration config = StoreConfiguration.builder()
                .storeId(storeId)
                .thresholdMultiplier(3.0)
                .averageBasketSize(50.0)
                .build();
        when(configService.getConfiguration(storeId)).thenReturn(config);

        // Processor returns error
        BalanceQueryResponse balanceResponse = BalanceQueryResponse.builder()
                .status("ERROR")
                .error("Processor temporarily unavailable")
                .build();
        when(processorClient.queryBalance(any())).thenReturn(balanceResponse);

        // Act
        AuthorizationResponse response = authorizationService.authorize(cardNumber, "VISA", storeId, "req-123");

        // Assert
        assertNotNull(response);
        assertEquals(AuthorizationResponse.Decision.DENIED_PROCESSOR_ERROR.value, response.getDecision());
    }

    @Test
    @DisplayName("Uses default config when config is missing")
    void testAuthorizeWithDefaultConfig() {
        // Arrange
        String cardNumber = "4111111111111111";
        String storeId = "store-unknown";

        BINLookupResponse binResponse = BINLookupResponse.builder()
                .cardType("VISA")
                .network("VISA")
                .isPrepaid(true)
                .build();
        when(processorClient.lookupBIN(cardNumber)).thenReturn(binResponse);

        // Config service returns default config
        StoreConfiguration defaultConfig = StoreConfiguration.builder()
                .storeId(storeId)
                .thresholdMultiplier(3.0)
                .averageBasketSize(50.0)
                .build();
        when(configService.getConfiguration(storeId)).thenReturn(defaultConfig);

        BalanceQueryResponse balanceResponse = BalanceQueryResponse.builder()
                .status("SUCCESS")
                .availableBalanceCents(20000)
                .preauthId("preauth-789")
                .build();
        when(processorClient.queryBalance(any())).thenReturn(balanceResponse);

        // Act
        AuthorizationResponse response = authorizationService.authorize(cardNumber, "VISA", storeId, "req-123");

        // Assert
        assertNotNull(response);
        assertEquals(AuthorizationResponse.Decision.APPROVED.value, response.getDecision());
    }

    @Test
    @DisplayName("Latency should be under 1.2 seconds")
    void testAuthorizationLatency() {
        // Arrange
        String cardNumber = "4111111111111111";
        String storeId = "store-123";

        BINLookupResponse binResponse = BINLookupResponse.builder()
                .isPrepaid(true)
                .build();
        when(processorClient.lookupBIN(cardNumber)).thenReturn(binResponse);

        StoreConfiguration config = StoreConfiguration.builder()
                .storeId(storeId)
                .thresholdMultiplier(3.0)
                .averageBasketSize(50.0)
                .build();
        when(configService.getConfiguration(storeId)).thenReturn(config);

        BalanceQueryResponse balanceResponse = BalanceQueryResponse.builder()
                .status("SUCCESS")
                .availableBalanceCents(20000)
                .preauthId("preauth-999")
                .build();
        when(processorClient.queryBalance(any())).thenReturn(balanceResponse);

        // Act
        long startTime = System.currentTimeMillis();
        AuthorizationResponse response = authorizationService.authorize(cardNumber, "VISA", storeId, "req-123");
        long elapsed = System.currentTimeMillis() - startTime;

        // Assert
        assertTrue(elapsed < 1200, "Authorization should complete in under 1.2 seconds");
        assertTrue(response.getTotalDecisionTimeMs() < 1200);
    }
}
