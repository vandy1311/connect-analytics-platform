package com.jwo.auth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import io.micrometer.core.instrument.MeterRegistry;

@SpringBootApplication
public class JwoAuthServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(JwoAuthServiceApplication.class, args);
    }

    @Bean
    public MeterRegistry meterRegistry() {
        return new io.micrometer.core.instrument.simple.SimpleMeterRegistry();
    }
}
