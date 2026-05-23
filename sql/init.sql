CREATE DATABASE IF NOT EXISTS ai_girlfriend
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_girlfriend;

-- 1. 角色
CREATE TABLE characters (
    id          VARCHAR(32)  PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL,
    avatar      VARCHAR(200) NOT NULL,
    voice       VARCHAR(100) DEFAULT 'longxiaochun',
    tts_model   VARCHAR(50)  DEFAULT 'cosyvoice-v3-flash',
    `group`     VARCHAR(20)  DEFAULT 'girlfriend',
    description VARCHAR(200) NOT NULL,
    is_active   TINYINT(1)   DEFAULT 1,
    sort_order  INT          DEFAULT 0,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 人设
CREATE TABLE character_personas (
    id             INT          AUTO_INCREMENT PRIMARY KEY,
    character_id   VARCHAR(32)  NOT NULL,
    base_prompt    TEXT         NOT NULL,
    emotion_styles JSON,
    intent_styles  JSON,
    created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    UNIQUE KEY uk_character (character_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 管理员
CREATE TABLE admin_users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50) NOT NULL UNIQUE,
    password    VARCHAR(64) NOT NULL,
    role        VARCHAR(20) DEFAULT 'admin',
    is_active   TINYINT(1)  DEFAULT 1,
    created_at  DATETIME    DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 用户
CREATE TABLE users (
    id          VARCHAR(32) PRIMARY KEY,
    openid      VARCHAR(64),
    nickname    VARCHAR(100),
    avatar_url  VARCHAR(500),
    is_active   TINYINT(1) DEFAULT 1,
    created_at  DATETIME   DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 对话
CREATE TABLE conversations (
    id            VARCHAR(32) PRIMARY KEY,
    user_id       VARCHAR(32),
    character_id  VARCHAR(32) DEFAULT 'sweet',
    title         VARCHAR(200) DEFAULT '新对话',
    message_count INT         DEFAULT 0,
    created_at    DATETIME    DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_char (character_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. 消息
CREATE TABLE messages (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id  VARCHAR(32) NOT NULL,
    role             VARCHAR(20) NOT NULL,
    content          TEXT        NOT NULL,
    emotion          VARCHAR(20),
    has_voice        TINYINT(1)  DEFAULT 0,
    voice_url        VARCHAR(500),
    created_at       DATETIME    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conv (conversation_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. 文档
CREATE TABLE documents (
    id          VARCHAR(32) PRIMARY KEY,
    file_name   VARCHAR(500) NOT NULL,
    file_type   VARCHAR(20)  NOT NULL,
    file_size   BIGINT       DEFAULT 0,
    chunk_count INT          DEFAULT 0,
    status      VARCHAR(20)  DEFAULT 'ready',
    uploaded_by VARCHAR(50),
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. 系统配置
CREATE TABLE system_config (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    config_key  VARCHAR(100) NOT NULL UNIQUE,
    config_val  TEXT         NOT NULL,
    description VARCHAR(200),
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
