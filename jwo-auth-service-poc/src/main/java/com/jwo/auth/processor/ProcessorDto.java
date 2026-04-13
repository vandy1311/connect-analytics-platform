package com.jwo.auth.processor;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Request to processor for balance query
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BalanceQueryRequest {
    private String cardToken;
    private long transactionAmountCents;
    private String storeId;
}

/**
 * Response from processor with balance
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BalanceQueryResponse {
    private String status; // SUCCESS, ERROR, TIMEOUT
    private Long availableBalanceCents;
    private String preauthId;
    private String error;

    public boolean isSuccess() {
        return "SUCCESS".equals(status);
    }
}

/**
 * Request to reverse a preauth
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PreauthReverseRequest {
    private String preauthId;
}

/**
 * Response from preauth reversal
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PreauthReverseResponse {
    private String status; // SUCCESS, ERROR, TIMEOUT
    private Long voidedAmountCents;
    private String error;

    public boolean isSuccess() {
        return "SUCCESS".equals(status);
    }
}

/**
 * BIN lookup response
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BINLookupResponse {
    private String cardType; // VISA, MASTERCARD, AMEX, etc.
    private String network;
    private boolean isPrepaid;
}
