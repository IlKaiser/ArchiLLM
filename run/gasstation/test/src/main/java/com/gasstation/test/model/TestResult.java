package com.gasstation.test.model;

public class TestResult {
    private TestCase testCase;
    private TestStatus status;
    private String expected;
    private String actual;
    private String error;
    private long durationMs;

    public TestResult() {}

    public TestResult(TestCase testCase, TestStatus status, String expected, String actual, String error, long durationMs) {
        this.testCase = testCase;
        this.status = status;
        this.expected = expected;
        this.actual = actual;
        this.error = error;
        this.durationMs = durationMs;
    }

    public TestCase getTestCase() { return testCase; }
    public void setTestCase(TestCase testCase) { this.testCase = testCase; }
    public TestStatus getStatus() { return status; }
    public void setStatus(TestStatus status) { this.status = status; }
    public String getExpected() { return expected; }
    public void setExpected(String expected) { this.expected = expected; }
    public String getActual() { return actual; }
    public void setActual(String actual) { this.actual = actual; }
    public String getError() { return error; }
    public void setError(String error) { this.error = error; }
    public long getDurationMs() { return durationMs; }
    public void setDurationMs(long durationMs) { this.durationMs = durationMs; }
}
