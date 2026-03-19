package com.gasstation.test;

import com.gasstation.test.model.TestReport;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

@Component
public class TestRunner implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(TestRunner.class);

    private final TestExecutor executor;
    private final ReportGenerator reportGenerator;

    public TestRunner(TestExecutor executor, ReportGenerator reportGenerator) {
        this.executor = executor;
        this.reportGenerator = reportGenerator;
    }

    @Override
    public void run(ApplicationArguments args) {
        log.info("=============================================================");
        log.info("  Gas Station – Tescav Test Suite");
        log.info("=============================================================");

        log.info("Executing test cases against backend...");
        TestReport report = executor.executeAll();

        log.info("=============================================================");
        log.info("  Results: {}/{} passed  ({} failed, {} error, {} skipped)",
                report.getPassedTests(), report.getTotalTests(),
                report.getFailedTests(), report.getErrorTests(), report.getSkippedTests());
        log.info("=============================================================");

        log.info("Generating reports...");
        reportGenerator.generateJsonReport(report);
        reportGenerator.generateHtmlReport(report);

        log.info("Done. Reports saved to: {}", System.getProperty("user.dir") + "/" + "run/gasstation/test");
    }
}
