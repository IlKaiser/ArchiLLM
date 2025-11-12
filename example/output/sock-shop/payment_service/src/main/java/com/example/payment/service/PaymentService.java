package com.example.payment.service;

import com.example.payment.domain.Payment;
import com.example.payment.domain.PaymentEvent;
import com.example.payment.domain.PaymentRepository;
import com.example.payment.saga.OrderPaymentSaga;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PaymentService {

    private final PaymentRepository paymentRepository;
    private final ApplicationEventPublisher eventPublisher;
    private final OrderPaymentSaga orderPaymentSaga;

    public PaymentService(PaymentRepository paymentRepository,
                         ApplicationEventPublisher eventPublisher,
                         OrderPaymentSaga orderPaymentSaga) {
        this.paymentRepository = paymentRepository;
        this.eventPublisher = eventPublisher;
        this.orderPaymentSaga = orderPaymentSaga;
    }

    @Transactional
    public Payment processPayment(Long orderId, Long amount) {
        // Create aggregate
        Payment payment = new Payment(orderId, amount);
        paymentRepository.save(payment);

        // Publish domain event
        PaymentEvent event = new PaymentEvent(payment.getId(), payment.getOrderId(), payment.getAmount(), "PAYMENT_CREATED");
        eventPublisher.publishEvent(event);

        // Start saga for order payment
        orderPaymentSaga.start(payment);

        return payment;
    }

    // TODO: Add methods for payment confirmation, refund, etc., as needed.
}