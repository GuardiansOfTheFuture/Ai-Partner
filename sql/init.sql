-- ═══════════════════════════════════════════
-- 小暖 AI · 数据库初始化
-- ═══════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS multi_agent
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE multi_agent;

-- ── 文档表 ──
CREATE TABLE IF NOT EXISTS documents (
    id          VARCHAR(32)  PRIMARY KEY   COMMENT '文档ID',
    file_name   VARCHAR(500) NOT NULL      COMMENT '原始文件名',
    file_type   VARCHAR(20)  NOT NULL      COMMENT '文件类型: pdf/docx/txt/md',
    chunk_count INT          DEFAULT 0     COMMENT '向量块数量',
    status      VARCHAR(20)  DEFAULT 'ready' COMMENT '状态: ready/deleted',
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档元数据';

-- ── 对话表 ──
CREATE TABLE IF NOT EXISTS conversations (
    id            VARCHAR(32)  PRIMARY KEY   COMMENT '对话ID',
    title         VARCHAR(200) DEFAULT '新对话',
    message_count INT          DEFAULT 0,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话';

-- ── 消息表 ──
CREATE TABLE IF NOT EXISTS messages (
    id              INT          AUTO_INCREMENT PRIMARY KEY,
    conversation_id VARCHAR(32)  NOT NULL COMMENT '所属对话ID',
    role            VARCHAR(20)  NOT NULL COMMENT 'user/assistant',
    content         TEXT         NOT NULL COMMENT '消息内容',
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conv_id (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息记录';
