package com.gasstation.test.model;

import java.util.List;

public class CriterionReport {
    private String criterion;
    private String description;
    private int totalTests;
    private int passedTests;
    private int failedTests;
    private int errorTests;
    private int skippedTests;
    private List<TestResult> results;

    public CriterionReport() {}

    public CriterionReport(String criterion, String description, List<TestResult> results) {
        this.criterion = criterion;
        this.description = description;
        this.results = results;
        this.totalTests = results.size();
        this.passedTests = (int) results.stream().filter(r -> r.getStatus() == TestStatus.PASS).count();
        this.failedTests = (int) results.stream().filter(r -> r.getStatus() == TestStatus.FAIL).count();
        this.errorTests  = (int) results.stream().filter(r -> r.getStatus() == TestStatus.ERROR).count();
        this.skippedTests = (int) results.stream().filter(r -> r.getStatus() == TestStatus.SKIP).count();
    }

    public String getCriterion() { return criterion; }
    public void setCriterion(String criterion) { this.criterion = criterion; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
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
    public List<TestResult> getResults() { return results; }
    public void setResults(List<TestResult> results) { this.results = results; }
}
