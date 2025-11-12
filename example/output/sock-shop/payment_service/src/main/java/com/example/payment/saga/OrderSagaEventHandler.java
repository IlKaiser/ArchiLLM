package com.example.payment.saga;

import com.example.payment.domain.Payment;
import com.example.payment.domain.PaymentRepository;
import com.example.payment.events.PaymentCompletedEvent;
import com.example.payment.events.PaymentFailedEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

// Handles saga-related events from the Order service.
@Component
public class OrderSagaEventHandler {

    private final PaymentRepository paymentRepository;

    @Autowired
    public OrderSagaEventHandler(PaymentRepository paymentRepository) {
        this.paymentRepository = paymentRepository;
    }

    // TODO: Replace with actual event/message listener integration (e.g., Kafka, messaging framework)
    @EventListener
    public void handleOrderPaymentRequested(OrderPaymentRequestedEvent event) {
        // Minimal stub: create a Payment aggregate and persist it
        Payment payment = new Payment(event.getOrderId(), event.getAmount());
        paymentRepository.save(payment);

        // TODO: Publish PaymentCompletedEvent or PaymentFailedEvent as needed
    }

    // Example event handler for payment completion (could be triggered by domain logic)
    @EventListener
    public void handlePaymentCompleted(PaymentCompletedEvent event) {
        // TODO: Notify Order saga of payment completion (e.g., send event/message)
    }

    // Example event handler for payment failure (could be triggered by domain logic)
    @EventListener
    public void handlePaymentFailed(PaymentFailedEvent event) {
        // TODO: Notify Order saga of payment failure (e.g., send event/message)
    }
}