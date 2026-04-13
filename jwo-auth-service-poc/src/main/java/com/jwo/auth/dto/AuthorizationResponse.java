package com.jwo.auth.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Authorization response DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AuthorizationResponse {
    @JsonProperty("decision")
    private String decision; // APPROVED, DENIED_INSUFFICIENT_BALANCE, DENIED_NOT_PREPAID, DENIED_TIMEOUT, DENIED_ERROR

    @JsonProperty("available_balance_cents")
    private Long availableBalanceCents;

    @JsonProperty("required_balance_cents")
    private Long requiredBalanceCents;

    @JsonProperty("total_decision_time_ms")
    private Long totalDecisionTimeMs;

    @JsonProperty("reason")
    private String reason;

    @JsonProperty("request_id")
    private String requestId;

    @JsonProperty("timestamp")
    private String timestamp;

    public enum Decision {
        APPROVED("approved"),
        DENIED_NOT_PREPAID("denied_not_prepaid"),
        DENIED_INSUFFICIENT_BALANCE("denied_insufficient_balance"),
        DENIED_TIMEOUT("denied_timeout"),
        DENIED_PROCESSOR_ERROR("denied_processor_error"),
        DENIED_NO_BALANCE("denied_no_balance"),
        DENIED_MISSING_CONFIG("denied_missing_config"),
        DENIED_INVALID_INPUT("denied_invalid_input");

        public final String value;

        Decision(String value) {
            this.value = value;
        }
    }
}
