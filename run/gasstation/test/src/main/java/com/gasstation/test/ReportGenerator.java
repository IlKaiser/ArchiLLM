package com.gasstation.test;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.gasstation.test.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.format.DateTimeFormatter;

@Component
public class ReportGenerator {

    private static final Logger log = LoggerFactory.getLogger(ReportGenerator.class);
    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final String outputDir;
    private final ObjectMapper mapper;

    public ReportGenerator(@Value("${report.output.dir:run/gasstation/test}") String outputDir) {
        this.outputDir = outputDir;
        this.mapper = new ObjectMapper()
                .registerModule(new JavaTimeModule())
                .enable(SerializationFeature.INDENT_OUTPUT)
                .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    }

    public void generateJsonReport(TestReport report) {
        try {
            Path dir = Path.of(outputDir);
            Files.createDirectories(dir);
            Path file = dir.resolve("report.json");
            mapper.writeValue(file.toFile(), report);
            log.info("JSON report written to: {}", file.toAbsolutePath());
        } catch (IOException e) {
            log.error("Failed to write report.json", e);
        }
    }

    public void generateHtmlReport(TestReport report) {
        try {
            Path dir = Path.of(outputDir);
            Files.createDirectories(dir);
            Path file = dir.resolve("report.html");
            try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(file))) {
                writeHtml(w, report);
            }
            log.info("HTML report written to: {}", file.toAbsolutePath());
        } catch (IOException e) {
            log.error("Failed to write report.html", e);
        }
    }

    private void writeHtml(PrintWriter w, TestReport report) {
        String runDate = report.getTestRunDate() != null
                ? report.getTestRunDate().format(FMT) : "N/A";

        w.println("<!DOCTYPE html>");
        w.println("<html lang=\"en\">");
        w.println("<head>");
        w.println("  <meta charset=\"UTF-8\">");
        w.println("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">");
        w.println("  <title>Gas Station – Test Report</title>");
        w.println("  <style>");
        w.println("    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; color: #333; }");
        w.println("    h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }");
        w.println("    h2 { color: #2980b9; margin-top: 30px; }");
        w.println("    h3 { color: #34495e; margin-top: 20px; }");
        w.println("    .summary { background: #fff; border-radius: 8px; padding: 20px; margin: 20px 0;");
        w.println("               box-shadow: 0 2px 4px rgba(0,0,0,0.1); }");
        w.println("    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));");
        w.println("                    gap: 15px; margin-top: 15px; }");
        w.println("    .metric { text-align: center; padding: 15px; border-radius: 6px; }");
        w.println("    .metric .value { font-size: 2em; font-weight: bold; }");
        w.println("    .metric .label { font-size: 0.85em; color: #666; }");
        w.println("    .total   { background: #ecf0f1; }");
        w.println("    .passed  { background: #d5f5e3; color: #1e8449; }");
        w.println("    .failed  { background: #fadbd8; color: #922b21; }");
        w.println("    .error   { background: #fdebd0; color: #935116; }");
        w.println("    .skipped { background: #eaf0fb; color: #2e4482; }");
        w.println("    .criterion { background: #fff; border-radius: 8px; padding: 20px; margin: 20px 0;");
        w.println("                 box-shadow: 0 2px 4px rgba(0,0,0,0.1); }");
        w.println("    .crit-stats { display: flex; gap: 15px; flex-wrap: wrap; margin: 10px 0; }");
        w.println("    .badge { padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold; }");
        w.println("    .badge-total   { background: #bdc3c7; }");
        w.println("    .badge-pass    { background: #d5f5e3; color: #1e8449; }");
        w.println("    .badge-fail    { background: #fadbd8; color: #922b21; }");
        w.println("    .badge-error   { background: #fdebd0; color: #935116; }");
        w.println("    .badge-skip    { background: #eaf0fb; color: #2e4482; }");
        w.println("    table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.9em; }");
        w.println("    th { background: #2c3e50; color: #fff; padding: 10px; text-align: left; }");
        w.println("    td { padding: 8px 10px; border-bottom: 1px solid #ecf0f1; vertical-align: top; }");
        w.println("    tr:nth-child(even) { background: #f9f9f9; }");
        w.println("    .status-PASS    { color: #1e8449; font-weight: bold; }");
        w.println("    .status-FAIL    { color: #922b21; font-weight: bold; }");
        w.println("    .status-ERROR   { color: #935116; font-weight: bold; }");
        w.println("    .status-SKIP    { color: #2e4482; font-weight: bold; }");
        w.println("    .progress-bar { height: 10px; background: #ecf0f1; border-radius: 5px; margin: 10px 0; }");
        w.println("    .progress-fill { height: 100%; border-radius: 5px; background: #27ae60; }");
        w.println("    .desc { font-style: italic; color: #666; margin: 5px 0 15px 0; }");
        w.println("    code { background: #f0f0f0; padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }");
        w.println("  </style>");
        w.println("</head>");
        w.println("<body>");

        w.println("  <h1>Gas Station – Test Execution Report</h1>");
        w.printf("  <p>Generated: <strong>%s</strong></p>%n", runDate);

        // Overall summary
        int total  = report.getTotalTests();
        int passed = report.getPassedTests();
        int failed = report.getFailedTests();
        int error  = report.getErrorTests();
        int skip   = report.getSkippedTests();
        double pct = total > 0 ? (100.0 * passed / total) : 0;

        w.println("  <div class=\"summary\">");
        w.println("    <h2 style=\"margin-top:0\">Overall Summary</h2>");
        w.printf("    <div class=\"progress-bar\"><div class=\"progress-fill\" style=\"width:%.1f%%\"></div></div>%n", pct);
        w.printf("    <p><strong>%.1f%%</strong> tests passed</p>%n", pct);
        w.println("    <div class=\"summary-grid\">");
        metricBox(w, "total",   "Total",   total);
        metricBox(w, "passed",  "Passed",  passed);
        metricBox(w, "failed",  "Failed",  failed);
        metricBox(w, "error",   "Error",   error);
        metricBox(w, "skipped", "Skipped", skip);
        w.println("    </div>");
        w.println("  </div>");

        // Test cases section
        w.println("  <h2>Test Cases by Criterion</h2>");

        for (CriterionReport cr : report.getCriteria()) {
            int ctotal  = cr.getTotalTests();
            int cpassed = cr.getPassedTests();
            int cfailed = cr.getFailedTests();
            int cerror  = cr.getErrorTests();
            int cskip   = cr.getSkippedTests();
            double cpct = ctotal > 0 ? (100.0 * cpassed / ctotal) : 0;

            w.println("  <div class=\"criterion\">");
            w.printf("    <h3>%s</h3>%n", escHtml(cr.getCriterion()));
            w.printf("    <p class=\"desc\">%s</p>%n", escHtml(cr.getDescription()));

            w.println("    <div class=\"crit-stats\">");
            w.printf("      <span class=\"badge badge-total\">Total: %d</span>%n", ctotal);
            w.printf("      <span class=\"badge badge-pass\">Passed: %d</span>%n", cpassed);
            w.printf("      <span class=\"badge badge-fail\">Failed: %d</span>%n", cfailed);
            w.printf("      <span class=\"badge badge-error\">Error: %d</span>%n", cerror);
            w.printf("      <span class=\"badge badge-skip\">Skipped: %d</span>%n", cskip);
            w.printf("      <span class=\"badge badge-pass\">%.1f%%</span>%n", cpct);
            w.println("    </div>");

            w.printf("    <div class=\"progress-bar\"><div class=\"progress-fill\" style=\"width:%.1f%%\"></div></div>%n", cpct);

            w.println("    <table>");
            w.println("      <thead>");
            w.println("        <tr>");
            w.println("          <th>ID</th>");
            w.println("          <th>Name</th>");
            w.println("          <th>Description</th>");
            w.println("          <th>Expected</th>");
            w.println("          <th>Actual</th>");
            w.println("          <th>Status</th>");
            w.println("          <th>ms</th>");
            w.println("        </tr>");
            w.println("      </thead>");
            w.println("      <tbody>");

            for (TestResult tr : cr.getResults()) {
                TestCase tc = tr.getTestCase();
                String st = tr.getStatus() != null ? tr.getStatus().name() : "UNKNOWN";
                String actual = tr.getActual() != null ? tr.getActual()
                        : (tr.getError() != null ? "ERROR: " + truncate(tr.getError(), 120) : "null");
                w.println("        <tr>");
                w.printf("          <td><code>%s</code></td>%n", escHtml(tc.getId()));
                w.printf("          <td>%s</td>%n", escHtml(tc.getName()));
                w.printf("          <td>%s</td>%n", escHtml(tc.getDescription()));
                w.printf("          <td><code>%s</code></td>%n", escHtml(str(tr.getExpected())));
                w.printf("          <td><code>%s</code></td>%n", escHtml(actual));
                w.printf("          <td class=\"status-%s\">%s</td>%n", st, st);
                w.printf("          <td>%d</td>%n", tr.getDurationMs());
                w.println("        </tr>");
            }

            w.println("      </tbody>");
            w.println("    </table>");
            w.println("  </div>");
        }

        w.println("</body>");
        w.println("</html>");
    }

    private void metricBox(PrintWriter w, String cssClass, String label, int value) {
        w.printf("      <div class=\"metric %s\">%n", cssClass);
        w.printf("        <div class=\"value\">%d</div>%n", value);
        w.printf("        <div class=\"label\">%s</div>%n", label);
        w.println("      </div>");
    }

    private String escHtml(String s) {
        if (s == null) return "";
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;");
    }

    private String str(String s) { return s != null ? s : ""; }

    private String truncate(String s, int max) {
        if (s == null) return "";
        return s.length() > max ? s.substring(0, max) + "…" : s;
    }
}
