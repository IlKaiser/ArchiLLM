package com.example.payment.saga;

import com.example.payment.domain.Payment;
import com.example.payment.domain.PaymentRepository;
import com.example.payment.events.PaymentCompletedEvent;
import com.example.payment.events.PaymentFailedEvent;
import com.example.payment.events.PaymentEvent;
import com.example.payment.service.PaymentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Component;

// This is a minimal stub for a saga participant in the Payment service
// that coordinates with the Order saga.

@Component
public class OrderPaymentSaga {

    private final PaymentService paymentService;
    private final ApplicationEventPublisher eventPublisher;

    @Autowired
    public OrderPaymentSaga(PaymentService paymentService,
                            ApplicationEventPublisher eventPublisher) {
        this.paymentService = paymentService;
        this.eventPublisher = eventPublisher;
    }

    /**
     * Called by the Order saga orchestrator to initiate payment.
     * In a real implementation, this would be triggered by a message or command.
     */
    public void handleOrderPayment(Long orderId, Long customerId, int amount) {
        // TODO: Validate order and customer existence (integration with Order/Customer service)
        Payment payment = paymentService.createPayment(orderId, customerId, amount);

        if (payment.isSuccessful()) {
            publishEvent(new PaymentCompletedEvent(orderId, payment.getId()));
        } else {
            publishEvent(new PaymentFailedEvent(orderId, payment.getId(), payment.getFailureReason()));
        }
    }

    private void publishEvent(PaymentEvent event) {
        // In a real implementation, this would publish a domain event to a message broker
        eventPublisher.publishEvent(event);
    }
}