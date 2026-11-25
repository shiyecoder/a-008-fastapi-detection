-- Webshell检测平台 - 表结构
CREATE DATABASE IF NOT EXISTS `webshell_platform` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `webshell_platform`;

DROP TABLE IF EXISTS sys_user;
CREATE TABLE sys_user (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  nickname VARCHAR(50),
  avatar VARCHAR(255),
  email VARCHAR(100),
  phone VARCHAR(20),
  status TINYINT DEFAULT 1,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS sys_role;
CREATE TABLE sys_role (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  code VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(255),
  status TINYINT DEFAULT 1,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS sys_menu;
CREATE TABLE sys_menu (
  id INT PRIMARY KEY AUTO_INCREMENT,
  parent_id INT DEFAULT 0,
  name VARCHAR(50) NOT NULL,
  path VARCHAR(255),
  component VARCHAR(255),
  icon VARCHAR(50),
  menu_type VARCHAR(20) DEFAULT 'menu',
  permission VARCHAR(100),
  sort INT DEFAULT 0,
  visible TINYINT DEFAULT 1,
  status TINYINT DEFAULT 1,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS sys_user_role;
CREATE TABLE sys_user_role (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  role_id INT NOT NULL,
  KEY idx_user (user_id),
  KEY idx_role (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS sys_role_menu;
CREATE TABLE sys_role_menu (
  id INT PRIMARY KEY AUTO_INCREMENT,
  role_id INT NOT NULL,
  menu_id INT NOT NULL,
  KEY idx_role (role_id),
  KEY idx_menu (menu_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS sys_log;
CREATE TABLE sys_log (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT,
  username VARCHAR(50),
  action_type VARCHAR(30),
  action_module VARCHAR(50),
  action_desc VARCHAR(500),
  ip VARCHAR(50),
  status TINYINT DEFAULT 1,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_user (user_id),
  KEY idx_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS detection_task;
CREATE TABLE detection_task (
  id INT PRIMARY KEY AUTO_INCREMENT,
  task_name VARCHAR(255),
  file_name VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  file_size BIGINT,
  file_hash VARCHAR(128),
  language VARCHAR(20),
  detect_type VARCHAR(20),
  status VARCHAR(20) DEFAULT 'pending',
  risk_level VARCHAR(20),
  score INT DEFAULT 0,
  creator VARCHAR(50),
  user_id INT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  finish_time DATETIME,
  KEY idx_create (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS detection_result;
CREATE TABLE detection_result (
  id INT PRIMARY KEY AUTO_INCREMENT,
  task_id INT NOT NULL,
  rule_type VARCHAR(50),
  rule_name VARCHAR(255),
  matched_content TEXT,
  line_no INT,
  severity VARCHAR(20),
  description VARCHAR(500),
  KEY idx_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS yara_rule;
CREATE TABLE yara_rule (
  id INT PRIMARY KEY AUTO_INCREMENT,
  rule_name VARCHAR(100) NOT NULL,
  language VARCHAR(20),
  severity VARCHAR(20),
  rule_content TEXT NOT NULL,
  description VARCHAR(500),
  hit_count INT DEFAULT 0,
  is_enabled TINYINT DEFAULT 1,
  creator VARCHAR(50),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS quarantine_file;
CREATE TABLE quarantine_file (
  id INT PRIMARY KEY AUTO_INCREMENT,
  task_id INT,
  file_name VARCHAR(255),
  original_path VARCHAR(500),
  quarantine_path VARCHAR(500),
  file_size BIGINT,
  file_hash VARCHAR(128),
  risk_level VARCHAR(20),
  status VARCHAR(20) DEFAULT 'quarantined',
  operator VARCHAR(50),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS alert;
CREATE TABLE alert (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255),
  alert_type VARCHAR(50),
  alert_level VARCHAR(20),
  source VARCHAR(100),
  source_id INT,
  description TEXT,
  status VARCHAR(20) DEFAULT 'pending',
  handler VARCHAR(50),
  handle_note TEXT,
  handle_time DATETIME,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_status (status),
  KEY idx_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS vuln_fix_mapping;
CREATE TABLE vuln_fix_mapping (
  id INT PRIMARY KEY AUTO_INCREMENT,
  vuln_name VARCHAR(255) NOT NULL,
  vuln_type VARCHAR(100),
  severity VARCHAR(20),
  description TEXT,
  fix_suggestion TEXT,
  reference_url VARCHAR(500),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS report;
CREATE TABLE report (
  id INT PRIMARY KEY AUTO_INCREMENT,
  report_name VARCHAR(255),
  report_type VARCHAR(20),
  start_date DATE,
  end_date DATE,
  content LONGTEXT,
  file_path VARCHAR(500),
  creator VARCHAR(50),
  user_id INT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
