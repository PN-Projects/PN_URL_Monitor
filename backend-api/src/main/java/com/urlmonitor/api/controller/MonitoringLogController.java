package com.urlmonitor.api.controller;

import com.urlmonitor.api.model.MonitoringLog;
import com.urlmonitor.api.repository.MonitoringLogRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/logs")
public class MonitoringLogController {

    private final MonitoringLogRepository repository;

    @Autowired
    public MonitoringLogController(MonitoringLogRepository repository) {
        this.repository = repository;
    }

    @PostMapping
    public ResponseEntity<MonitoringLog> createLog(@RequestBody MonitoringLog log) {
        MonitoringLog savedLog = repository.save(log);
        return ResponseEntity.ok(savedLog);
    }

    @GetMapping
    public ResponseEntity<List<MonitoringLog>> getAllLogs() {
        List<MonitoringLog> logs = repository.findAll();
        return ResponseEntity.ok(logs);
    }
} 