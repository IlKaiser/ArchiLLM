package com.gasstation.test.model;

import java.time.LocalDateTime;
import java.util.List;

public class TestReport {
    private LocalDateTime testRunDate;
    private int totalTests;
    private int passedTests;
    private int failedTests;
    private int errorTests;
    private int skippedTests;
    private List<CriterionReport> criteria;

    public TestReport() {}

    public TestReport(List<CriterionReport> criteria) {
        this.testRunDate = LocalDateTime.now();
        this.criteria = criteria;
        this.totalTests = criteria.stream().mapToInt(CriterionReport::getTotalTests).sum();
        this.passedTests = criteria.stream().mapToInt(CriterionReport::getPassedTests).sum();
        this.failedTests = criteria.stream().mapToInt(CriterionReport::getFailedTests).sum();
        this.errorTests  = criteria.stream().mapToInt(CriterionReport::getErrorTests).sum();
        this.skippedTests = criteria.stream().mapToInt(CriterionReport::getSkippedTests).sum();
    }

    public LocalDateTime getTestRunDate() { return testRunDate; }
    public void setTestRunDate(LocalDateTime testRunDate) { this.testRunDate = testRunDate; }
    public int getTotalTests() { return totalTests; }
    public void setTotalTests(int totalTests) { this.totalTests = totalTests; }
    public int getPassedTests() { return passedTests; }
    public void setPassedTests(int passedTests) { this.passedTests = passedTests; }
    public int getFailedTests() { return failedTests; }
    public void setFailedTests(int failedTests) { this.failedTests = failedTests; }
    public int getErrorTests() { return errorTests; }
    public void setErrorTests(int errorTests) { this.errorTests = errorTests; }
    public int getSkippedTests() { return skippedTests; }
    public void setSkippedTests(int skippedTests) { this.skippedTests = skippedTests; }
    public List<CriterionReport> getCriteria() { return criteria; }
    public void setCriteria(List<CriterionReport> criteria) { this.criteria = criteria; }
}
