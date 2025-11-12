package com.example.logging.service;

import com.example.logging.model.LogEvent;
import com.example.logging.repository.LogRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class LogService {
    @Autowired
    private LogRepository logRepository;

    public LogEvent recordLog(LogEvent logEvent) {
        logEvent.setTimestamp(LocalDateTime.now());
        return logRepository.save(logEvent);
    }

    public List<LogEvent> getLogs(String filter, String dateRange, String service) {
        // For simplicity, return all logs. Filtering can be implemented as needed.
        return logRepository.findAll();
    }
}