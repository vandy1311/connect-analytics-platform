package com.jwo.auth.service;

import org.springframework.stereotype.Service;
import lombok.extern.slf4j.Slf4j;
import com.jwo.auth.dto.AuthorizationResponse;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.List;

/**
 * Event logger for authorization events
 * Logs events without sensitive data (PCI-DSS compliant)
 */
@Service
@Slf4j
public class EventLogger {

    private final List<AuthorizationEventRecord> eventLog = new CopyOnWriteArrayList<>();

    public void logAuthorizationEvent(AuthorizationResponse response) {
        AuthorizationEventRecord event = AuthorizationEventRecord.builder()
                .eventId(String.valueOf(System.currentTimeMillis()))
                .decision(response.getDecision())
                .availableBalanceCents(response.getAvailableBalanceCents())
                .requiredBalanceCents(response.getRequiredBalanceCents())
                .decisionTimeMs(response.getTotalDecisionTimeMs())
                .requestId(response.getRequestId())
                .timestamp(response.getTimestamp())
                .build();

        eventLog.add(event);
        
        // Log to console (no sensitive data)
        log.info("EVENT decision={} available={} required={} time={}ms requestId={}",
                event.decision,
                event.availableBalanceCents,
                event.requiredBalanceCents,
                event.decisionTimeMs,
                event.requestId);
    }

    /**
     * Get all events (for testing/monitoring)
     */
    public List<AuthorizationEventRecord> getEvents() {
        return new CopyOnWriteArrayList<>(eventLog);
    }

    /**
     * Clear event log (for testing)
     */
    public void clearEvents() {
        eventLog.clear();
    }

    /**
     * Internal event record class
     */
    @lombok.Data
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    @lombok.Builder
    public static class AuthorizationEventRecord {
        private String eventId;
        private String decision;
        private Long availableBalanceCents;
        private Long requiredBalanceCents;
        private Long decisionTimeMs;
        private String requestId;
        private String timestamp;
    }
}
