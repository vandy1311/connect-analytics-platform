package com.jwo.auth.processor;

/**
 * Interface for payment processor client
 * This abstraction allows swapping different processor implementations
 */
public interface PaymentProcessorClient {

    /**
     * Query balance from processor
     * @param request Balance query request
     * @return Balance query response
     */
    BalanceQueryResponse queryBalance(BalanceQueryRequest request);

    /**
     * Reverse a preauthorization
     * @param request Preauth reversal request
     * @return Reversal response
     */
    PreauthReverseResponse reversePreauth(PreauthReverseRequest request);

    /**
     * Lookup BIN to determine if card is prepaid
     * @param cardNumber Card number (or first 6 digits)
     * @return BIN lookup response
     */
    BINLookupResponse lookupBIN(String cardNumber);
}
