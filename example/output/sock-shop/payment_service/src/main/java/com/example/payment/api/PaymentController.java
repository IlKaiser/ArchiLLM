package com.example.payment.api;

import com.example.payment.domain.Payment;
import com.example.payment.domain.PaymentService;
import com.example.payment.domain.PaymentEvent;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/payments")
public class PaymentController {

    private final PaymentService paymentService;

    public PaymentController(PaymentService paymentService) {
        this.paymentService = paymentService;
    }

    @PostMapping
    public ResponseEntity<Payment> createPayment(@RequestBody CreatePaymentRequest request) {
        Payment payment = paymentService.createPayment(request.getOrderId(), request.getAmount());
        return ResponseEntity.ok(payment);
    }

    @GetMapping("/{paymentId}")
    public ResponseEntity<Payment> getPayment(@PathVariable Long paymentId) {
        Payment payment = paymentService.getPayment(paymentId);
        if (payment == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(payment);
    }

    @GetMapping("/{paymentId}/events")
    public ResponseEntity<List<PaymentEvent>> getPaymentEvents(@PathVariable Long paymentId) {
        List<PaymentEvent> events = paymentService.getPaymentEvents(paymentId);
        return ResponseEntity.ok(events);
    }

    // TODO: Add endpoints for saga orchestration callbacks if needed

    public static class CreatePaymentRequest {
        private Long orderId;
        private int amount;

        public Long getOrderId() {
            return orderId;
        }

        public void setOrderId(Long orderId) {
            this.orderId = orderId;
        }

        public int getAmount() {
            return amount;
        }

        public void setAmount(int amount) {
            this.amount = amount;
        }
    }
}