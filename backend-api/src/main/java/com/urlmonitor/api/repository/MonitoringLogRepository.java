package com.urlmonitor.api.repository;

import com.urlmonitor.api.model.MonitoringLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface MonitoringLogRepository extends JpaRepository<MonitoringLog, Long> {
} 