package com.gasstation.test;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class ApiClient {

    private static final Pattern ID_PATTERN    = Pattern.compile("\"id\"\\s*:\\s*(\\d+)");
    private static final Pattern STATE_PATTERN = Pattern.compile("\"state\"\\s*:\\s*\"([A-Z_]+)\"");
    private static final int MAX_BODY_BYTES = 8192; // only read first 8 KB of response

    private final ObjectMapper objectMapper;
    private final String baseUrl;

    public ApiClient(@Value("${backend.url:http://localhost:8080/api}") String baseUrl) {
        this.objectMapper = new ObjectMapper();
        this.baseUrl = baseUrl;
    }

    // -------- GasStation --------

    public ApiResponse createGasStation(String name) {
        return post("/gasstations", Map.of("name", name));
    }

    public ApiResponse approvePlans(Long id) {
        return post("/gasstations/" + id + "/approve-plans", null);
    }

    public ApiResponse rejectPlans(Long id) {
        return post("/gasstations/" + id + "/reject-plans", null);
    }

    public ApiResponse revisePlans(Long id) {
        return post("/gasstations/" + id + "/revise-plans", null);
    }

    public ApiResponse openingInspectionPassed(Long id) {
        return post("/gasstations/" + id + "/opening-inspection-passed", null);
    }

    public ApiResponse openingInspectionNotPassed(Long id) {
        return post("/gasstations/" + id + "/opening-inspection-not-passed", null);
    }

    public ApiResponse openStation(Long id) {
        return post("/gasstations/" + id + "/open", null);
    }

    public ApiResponse closeStation(Long id) {
        return post("/gasstations/" + id + "/close", null);
    }

    public ApiResponse startInspection(Long id) {
        return post("/gasstations/" + id + "/start-inspection", null);
    }

    public ApiResponse closingInspectionPassed(Long id) {
        return post("/gasstations/" + id + "/closing-inspection-passed", null);
    }

    public ApiResponse closingInspectionNotPassed(Long id) {
        return post("/gasstations/" + id + "/closing-inspection-not-passed", null);
    }

    public ApiResponse deleteGasStation(Long id) {
        return delete("/gasstations/" + id);
    }

    public ApiResponse getGasStation(Long id) {
        return get("/gasstations/" + id);
    }

    // -------- Pump --------

    public ApiResponse createPump(Long gasStationId, String name, String gasolineType,
                                  double tankCapacity, double reorderLevel, double criticalLevel) {
        return post("/pumps", Map.of(
                "gasStationId", gasStationId,
                "name", name,
                "gasolineType", gasolineType,
                "tankCapacity", tankCapacity,
                "reorderLevel", reorderLevel,
                "criticalLevel", criticalLevel
        ));
    }

    public ApiResponse blockPump(Long id) {
        return post("/pumps/" + id + "/block", null);
    }

    public ApiResponse releasePump(Long id) {
        return post("/pumps/" + id + "/release", null);
    }

    public ApiResponse refillPump(Long id, double amount) {
        return post("/pumps/" + id + "/refill", Map.of("amount", amount));
    }

    public ApiResponse deletePump(Long id) {
        return delete("/pumps/" + id);
    }

    public ApiResponse getPump(Long id) {
        return get("/pumps/" + id);
    }

    // -------- CashTurn --------

    public ApiResponse takeNozzleCash(Long pumpId, String name) {
        return post("/cashturns/take-nozzle-cash", Map.of("pumpId", pumpId, "name", name));
    }

    public ApiResponse scanCreditCard(Long pumpId, String name, String creditCardNumber) {
        return post("/cashturns/scan-credit-card", Map.of(
                "pumpId", pumpId, "name", name, "creditCardNumber", creditCardNumber));
    }

    public ApiResponse takeNozzleCredit(Long cashTurnId) {
        return post("/cashturns/" + cashTurnId + "/take-nozzle-credit", null);
    }

    public ApiResponse putBackNozzleCash(Long cashTurnId, double fuelAmount, double amount) {
        return post("/cashturns/" + cashTurnId + "/put-back-nozzle",
                Map.of("fuelAmount", fuelAmount, "amount", amount));
    }

    public ApiResponse payCash(Long cashTurnId) {
        return post("/cashturns/" + cashTurnId + "/pay-cash", null);
    }

    public ApiResponse chargeCreditCard(Long cashTurnId) {
        return post("/cashturns/" + cashTurnId + "/charge-credit-card", null);
    }

    public ApiResponse driveAwayWithoutPaying(Long cashTurnId) {
        return post("/cashturns/" + cashTurnId + "/drive-away-without-paying", null);
    }

    public ApiResponse endCashTurn(Long cashTurnId) {
        return post("/cashturns/" + cashTurnId + "/end", null);
    }

    public ApiResponse cancelCashTurn(Long cashTurnId) {
        return post("/cashturns/" + cashTurnId + "/cancel", null);
    }

    public ApiResponse deleteCashTurn(Long id) {
        return delete("/cashturns/" + id);
    }

    public ApiResponse getCashTurn(Long id) {
        return get("/cashturns/" + id);
    }

    // -------- RefuelTurn --------

    public ApiResponse createRefuelTurn(Long pumpId, Long cardHolderId, String name) {
        return post("/refuelturns", Map.of(
                "pumpId", pumpId, "cardHolderId", cardHolderId, "name", name));
    }

    public ApiResponse takeNozzleRefuel(Long refuelTurnId) {
        return post("/refuelturns/" + refuelTurnId + "/take-nozzle", null);
    }

    public ApiResponse putBackNozzleRefuel(Long refuelTurnId, double fuelAmount, double amount) {
        return post("/refuelturns/" + refuelTurnId + "/put-back-nozzle",
                Map.of("fuelAmount", fuelAmount, "amount", amount));
    }

    public ApiResponse cancelRefuelTurn(Long refuelTurnId) {
        return post("/refuelturns/" + refuelTurnId + "/cancel", null);
    }

    public ApiResponse endRefuelTurn(Long refuelTurnId) {
        return post("/refuelturns/" + refuelTurnId + "/end", null);
    }

    public ApiResponse deleteRefuelTurn(Long id) {
        return delete("/refuelturns/" + id);
    }

    public ApiResponse getRefuelTurn(Long id) {
        return get("/refuelturns/" + id);
    }

    // -------- CardHolder --------

    public ApiResponse createCardHolder(String name, String email, boolean isGoodCustomer) {
        return post("/cardholders", Map.of(
                "name", name, "email", email,
                "phone", "555-0100", "address", "Test Street",
                "isGoodCustomer", isGoodCustomer));
    }

    public ApiResponse suspendCardHolder(Long id) {
        return post("/cardholders/" + id + "/suspend", null);
    }

    public ApiResponse unsuspendCardHolder(Long id) {
        return post("/cardholders/" + id + "/unsuspend", null);
    }

    public ApiResponse deleteCardHolder(Long id) {
        return delete("/cardholders/" + id);
    }

    public ApiResponse getCardHolder(Long id) {
        return get("/cardholders/" + id);
    }

    // -------- Invoice --------

    public ApiResponse createInvoice(Long cardHolderId, String name, int month, int year) {
        return post("/invoices", Map.of(
                "cardHolderId", cardHolderId, "name", name,
                "month", month, "year", year));
    }

    public ApiResponse sendInvoice(Long invoiceId) {
        return post("/invoices/" + invoiceId + "/send", null);
    }

    public ApiResponse payInvoice(Long invoiceId) {
        return post("/invoices/" + invoiceId + "/pay", null);
    }

    public ApiResponse defaultOnInvoice(Long invoiceId) {
        return post("/invoices/" + invoiceId + "/default", null);
    }

    public ApiResponse endInvoice(Long invoiceId) {
        return post("/invoices/" + invoiceId + "/end", null);
    }

    public ApiResponse addInvoiceLine(Long invoiceId, Long invoiceLineId) {
        return post("/invoices/" + invoiceId + "/add-line", Map.of("invoiceLineId", invoiceLineId));
    }

    public ApiResponse deleteInvoice(Long id) {
        return delete("/invoices/" + id);
    }

    public ApiResponse getInvoice(Long id) {
        return get("/invoices/" + id);
    }

    // -------- InvoiceLine --------

    public ApiResponse createInvoiceLine(Long refuelTurnId, String name, double unitPrice) {
        return post("/invoicelines", Map.of(
                "refuelTurnId", refuelTurnId, "name", name, "unitPrice", unitPrice));
    }

    public ApiResponse endInvoiceLine(Long invoiceLineId) {
        return post("/invoicelines/" + invoiceLineId + "/end", null);
    }

    public ApiResponse deleteInvoiceLine(Long id) {
        return delete("/invoicelines/" + id);
    }

    public ApiResponse getInvoiceLine(Long id) {
        return get("/invoicelines/" + id);
    }

    // -------- HTTP helpers --------

    private ApiResponse post(String path, Object body) {
        return httpRequest("POST", path, body);
    }

    private ApiResponse get(String path) {
        return httpRequest("GET", path, null);
    }

    private ApiResponse delete(String path) {
        return httpRequest("DELETE", path, null);
    }

    /**
     * Executes an HTTP request, reads at most MAX_BODY_BYTES bytes from the response body,
     * then tries to parse the partial body as JSON. If JSON parsing fails (e.g. due to
     * the backend's circular-reference StackOverflow), it extracts id/state via regex.
     */
    @SuppressWarnings("unchecked")
    private ApiResponse httpRequest(String method, String path, Object body) {
        HttpURLConnection conn = null;
        try {
            URL url = new URL(baseUrl + path);
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod(method);
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setRequestProperty("Accept", "application/json");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(10000);

            if (body != null) {
                conn.setDoOutput(true);
                byte[] bodyBytes = objectMapper.writeValueAsBytes(body);
                conn.getOutputStream().write(bodyBytes);
                conn.getOutputStream().flush();
            }

            int status = conn.getResponseCode();
            InputStream is = status < 400 ? conn.getInputStream() : conn.getErrorStream();

            String snippet = "";
            if (is != null) {
                byte[] buf = new byte[MAX_BODY_BYTES];
                int n = 0, total = 0;
                while (total < MAX_BODY_BYTES && (n = is.read(buf, total, MAX_BODY_BYTES - total)) != -1) {
                    total += n;
                }
                // drain rest without reading into memory
                try { is.close(); } catch (IOException ignored) {}
                snippet = new String(buf, 0, total, "UTF-8");
            }

            if (status >= 400 || snippet.isEmpty()) {
                return new ApiResponse(status, null, snippet.isEmpty() ? "HTTP " + status : snippet);
            }

            // Try to parse as full JSON
            try {
                Map<String, Object> parsed = objectMapper.readValue(snippet, Map.class);
                return new ApiResponse(status, parsed, null);
            } catch (Exception jsonEx) {
                // Partial / malformed JSON – extract id + state via regex
                Map<String, Object> partial = new HashMap<>();
                Matcher idM = ID_PATTERN.matcher(snippet);
                if (idM.find()) partial.put("id", Long.parseLong(idM.group(1)));
                Matcher stM = STATE_PATTERN.matcher(snippet);
                if (stM.find()) partial.put("state", stM.group(1));
                if (!partial.isEmpty()) {
                    return new ApiResponse(status, partial,
                            "Partial JSON (circular ref or truncation): " + jsonEx.getMessage());
                }
                return new ApiResponse(status, null,
                        "Malformed JSON response: " + jsonEx.getMessage());
            }

        } catch (Exception ex) {
            return new ApiResponse(0, null, ex.getMessage());
        } finally {
            if (conn != null) conn.disconnect();
        }
    }

    // -------- Response wrapper --------

    public static class ApiResponse {
        private final int statusCode;
        private final Map<String, Object> body;
        private final String errorMessage;

        public ApiResponse(int statusCode, Map<String, Object> body, String errorMessage) {
            this.statusCode = statusCode;
            this.body = body;
            this.errorMessage = errorMessage;
        }

        public boolean isSuccess() { return statusCode >= 200 && statusCode < 300; }
        public int getStatusCode() { return statusCode; }
        public Map<String, Object> getBody() { return body; }
        public String getErrorMessage() { return errorMessage; }

        public Long getId() {
            if (body == null) return null;
            Object id = body.get("id");
            if (id instanceof Number) return ((Number) id).longValue();
            return null;
        }

        public String getState() {
            if (body == null) return null;
            Object state = body.get("state");
            return state != null ? state.toString() : null;
        }
    }
}
