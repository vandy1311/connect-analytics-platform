package com.jwo.auth.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Authorization request DTO for checking customer entry
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AuthorizationRequest {
    @JsonProperty("store_id")
    private String storeId;

    @JsonProperty("card_data")
    private CardData cardData;

    @JsonProperty("request_id")
    private String requestId;
}

/**
 * Card data DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
class CardData {
    @JsonProperty("card_number")
    private String cardNumber;

    @JsonProperty("card_network")
    private String cardNetwork;

    @JsonProperty("card_last_4")
    private String cardLast4;
}
