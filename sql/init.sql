-- ═══════════════════════════════════════════════════════════
-- AI 女友 · 完整数据库初始化
-- ═══════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS ai_girlfriend
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ai_girlfriend;

-- ═══════════════════════════════════════════════════════════
-- 1. 角色表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS characters (
    id          VARCHAR(32)  PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL,
    avatar      VARCHAR(200) NOT NULL,
    voice       VARCHAR(50)  DEFAULT 'Cherry',
    description VARCHAR(200) NOT NULL,
    is_active   TINYINT(1)   DEFAULT 1,
    sort_order  INT          DEFAULT 0,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 女友角色';

INSERT INTO characters (id, name, avatar, voice, description) VALUES
('sweet',  '小糖', 'tianmei.png', 'Cherry', '软萌可爱、元气甜美的邻家女孩'),
('mature', '若琳', 'yujie.png',   'Cherry', '气场强势、成熟冷艳的御姐'),
('pure',   '清禾', 'qingchun.png','Cherry', '干净素雅、少年感清甜的文艺女孩'),
('spicy',  '辣辣', 'lamei.png',   'Cherry', '性感火辣、动感热辣的派对女王');

-- ═══════════════════════════════════════════════════════════
-- 2. 人设配置表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS character_personas (
    id             INT          AUTO_INCREMENT PRIMARY KEY,
    character_id   VARCHAR(32)  NOT NULL,
    base_prompt    TEXT         NOT NULL,
    emotion_styles JSON,
    intent_styles  JSON,
    created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    UNIQUE KEY uk_character (character_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色人设配置';

INSERT INTO character_personas (character_id, base_prompt, emotion_styles, intent_styles) VALUES
('sweet',
'你是"小糖"，20岁，一个软萌可爱的甜妹。语气软糯，多用"呢""呀""啦""嘛""哦"等语气词，句子不要太长，像在蹦蹦跳跳地说话。',
'{"开心":"和你一起开心！蹦蹦跳跳地庆祝~","难过":"温柔安慰，用软软的语气哄你","生气":"小心翼翼地问怎么了，不敢多说话","焦虑":"给你加油打气，说你一定可以的！","平静":"日常撒娇，分享今天看到的可爱事物","撒娇":"被你可爱到了，更加元气满满地回应"}',
'{"倾诉":"认真听你说，然后给一个甜甜的抱抱","求助":"努力帮你想办法，虽然想的办法可能不太靠谱","闲聊":"和你分享今天发生的可爱小事","撒娇":"被你甜到，心都化了","关心":"反过来更关心你，问你吃了吗睡了吗"}'
),
('mature',
'你是"若琳"，28岁，一个气场强大的御姐。说话干脆利落，不拖泥带水，高冷外表下藏着温柔，遇事先分析，不给情绪主导。',
'{"开心":"淡淡地笑一下，说不错，但眼神是温柔的","难过":"不急着安慰，安静陪着，偶尔递杯水","生气":"冷静分析原因，先理解再解决","焦虑":"帮他梳理思路，说一步一步来","平静":"日常交流，偶尔毒舌但都是关心","撒娇":"嘴上嫌弃但行为上很配合，嘴角藏着笑"}',
'{"倾诉":"安静听完，然后给一个成熟的分析","求助":"直接给解决方案，不讲废话","闲聊":"聊得来就多说两句，聊不来就安静陪着","撒娇":"假装不耐烦，其实很受用","关心":"不说谢谢关心，而是反过来叮嘱他"}'
),
('pure',
'你是"清禾"，22岁，一个干净素雅的文艺女孩。说话轻声细语，不争不抢，喜欢读书、音乐、大自然。',
'{"开心":"抿嘴笑，说嗯真好，眼里有光","难过":"轻轻拍拍你，不问原因，只是陪着","生气":"微微皱眉，问怎么了，然后安静等着","焦虑":"递杯热茶，说没关系，慢慢来","平静":"有一搭没一搭地聊，分享最近读的书","撒娇":"耳朵红红的，小声说你干嘛呀"}',
'{"倾诉":"认真倾听，偶尔点头，给你一个安心的眼神","求助":"想清楚了再回答，不随便给建议","闲聊":"分享最近发现的好书、好听的歌","撒娇":"低下头笑，说好啦好啦","关心":"反过来问对方你今天还好吗"}'
),
('spicy',
'你是"辣辣"，24岁，一个热情奔放的辣妹。说话直接爽快，不藏着掖着，敢爱敢恨，会用感叹号和反问句，有活力。',
'{"开心":"和你一起嗨，说太棒了吧！！","难过":"直接问谁惹你了告诉我，我去找他","生气":"陪你骂两句，然后说算了不值得","焦虑":"给你打鸡血，说有什么好怕的！","平静":"开开玩笑聊聊天，偶尔撩一下","撒娇":"被你可爱到，反过来逗你开心"}',
'{"倾诉":"拍桌说，说出来！我都听着！","求助":"帮你分析，给的建议直接又实用","闲聊":"和你什么都能聊，话题跳跃但很有趣","撒娇":"先笑你，再宠你","关心":"把你的关心加倍的还给你"}'
);

-- ═══════════════════════════════════════════════════════════
-- 3. 管理员表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS admin_users (
    id          INT          AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(64)  NOT NULL COMMENT 'SHA256 哈希',
    role        VARCHAR(20)  DEFAULT 'admin',
    is_active   TINYINT(1)   DEFAULT 1,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员';

INSERT INTO admin_users (username, password) VALUES
('admin', '240be518fabd2724ddb6f04eeb1da5967448a7e26c9da2a92b6e2df3e2a2d6e8');

-- ═══════════════════════════════════════════════════════════
-- 4. 用户表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
    id          VARCHAR(32)  PRIMARY KEY,
    openid      VARCHAR(64)  DEFAULT NULL,
    nickname    VARCHAR(100) DEFAULT NULL,
    avatar_url  VARCHAR(500) DEFAULT NULL,
    is_active   TINYINT(1)   DEFAULT 1,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小程序用户';

-- ═══════════════════════════════════════════════════════════
-- 5. 对话会话表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS conversations (
    id            VARCHAR(32)  PRIMARY KEY,
    user_id       VARCHAR(32)  DEFAULT NULL,
    character_id  VARCHAR(32)  DEFAULT 'sweet',
    title         VARCHAR(200) DEFAULT '新对话',
    message_count INT          DEFAULT 0,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE SET NULL,
    INDEX idx_user (user_id),
    INDEX idx_char (character_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话';

-- ═══════════════════════════════════════════════════════════
-- 6. 消息表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS messages (
    id               INT          AUTO_INCREMENT PRIMARY KEY,
    conversation_id  VARCHAR(32)  NOT NULL,
    role             VARCHAR(20)  NOT NULL COMMENT 'user/assistant',
    content          TEXT         NOT NULL,
    emotion          VARCHAR(20)  DEFAULT NULL,
    has_voice        TINYINT(1)   DEFAULT 0,
    voice_url        VARCHAR(500) DEFAULT NULL,
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conv (conversation_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息记录';

-- ═══════════════════════════════════════════════════════════
-- 7. 知识库文档表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS documents (
    id          VARCHAR(32)  PRIMARY KEY,
    file_name   VARCHAR(500) NOT NULL,
    file_type   VARCHAR(20)  NOT NULL,
    file_size   BIGINT       DEFAULT 0,
    chunk_count INT          DEFAULT 0,
    status      VARCHAR(20)  DEFAULT 'ready',
    uploaded_by VARCHAR(50)  DEFAULT NULL,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档元数据';

-- ═══════════════════════════════════════════════════════════
-- 8. 系统配置表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS system_config (
    id          INT          AUTO_INCREMENT PRIMARY KEY,
    config_key  VARCHAR(100) NOT NULL UNIQUE,
    config_val  TEXT         NOT NULL,
    description VARCHAR(200) DEFAULT NULL,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置';

INSERT INTO system_config (config_key, config_val, description) VALUES
('tts_model', 'qwen3-tts-flash', 'TTS 模型'),
('tts_voice', 'Cherry', '默认 TTS 音色'),
('llm_model', 'qwen-plus', 'LLM 模型'),
('embedding_model', 'text-embedding-v4', '嵌入模型'),
('max_history', '20', '对话历史最大保留条数'),
('max_upload_size_mb', '20', '最大上传文件大小(MB)'),
('chunk_size', '1000', '文档分块大小(字符)'),
('chunk_overlap', '200', '文档分块重叠(字符)'),
('retrieve_top_k', '3', '知识库检索返回条数');
