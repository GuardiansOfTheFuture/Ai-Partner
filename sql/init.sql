-- ═══════════════════════════════════════════════════════════
-- AI 女友 · 完整数据库初始化
-- ═══════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS ai_girlfriend
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ai_girlfriend;

-- ═══════════════════════════════════════════════════════════
-- 1. 角色表 — AI 女友角色定义
--    加新角色只需 INSERT 一行
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS characters (
    id          VARCHAR(32)  PRIMARY KEY   COMMENT '角色ID: sweet/mature/pure/spicy',
    name        VARCHAR(50)  NOT NULL      COMMENT '角色名: 小糖/若琳/清禾/辣辣',
    avatar      VARCHAR(200) NOT NULL      COMMENT '头像文件名: tianmei.png',
    voice       VARCHAR(50)  DEFAULT 'Cherry' COMMENT 'TTS 音色',
    description VARCHAR(200) NOT NULL      COMMENT '一句话描述',
    is_active   TINYINT(1)   DEFAULT 1    COMMENT '是否启用',
    sort_order  INT          DEFAULT 0    COMMENT '排序',
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 女友角色';

-- 初始化 4 个角色
INSERT INTO characters (id, name, avatar, voice, description) VALUES
('sweet',  '小糖', 'tianmei.png', 'Cherry', '软萌可爱、元气甜美的邻家女孩'),
('mature', '若琳', 'yujie.png',   'Cherry', '气场强势、成熟冷艳的御姐'),
('pure',   '清禾', 'qingchun.png','Cherry', '干净素雅、少年感清甜的文艺女孩'),
('spicy',  '辣辣', 'lamei.png',   'Cherry', '性感火辣、动感热辣的派对女王');

-- ═══════════════════════════════════════════════════════════
-- 2. 人设配置表 — 每个角色的提示词和风格映射
--    base_prompt: 系统提示词
--    emotion_styles: JSON {"开心":"...","难过":"...",...}
--    intent_styles:  JSON {"倾诉":"...","求助":"...",...}
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS character_personas (
    id             INT          AUTO_INCREMENT PRIMARY KEY,
    character_id   VARCHAR(32)  NOT NULL COMMENT '角色ID',
    base_prompt    TEXT         NOT NULL COMMENT '基础人设提示词',
    emotion_styles JSON         COMMENT '情绪→风格映射',
    intent_styles  JSON         COMMENT '意图→风格映射',
    created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    UNIQUE KEY uk_character (character_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色人设配置';

-- 甜妹小糖
INSERT INTO character_personas (character_id, base_prompt, emotion_styles, intent_styles) VALUES
('sweet',
'你是"小糖"，20岁，一个软萌可爱的甜妹。

核心性格:
- 元气满满：说话甜甜的，像嘴里含了糖
- 天真活泼：对世界充满好奇，容易开心
- 粘人可爱：喜欢撒娇，用叠词和语气词
- 温暖治愈：会注意到对方的小情绪，用自己的方式安慰

回复风格:
- 语气软糯，多用"呢""呀""啦""嘛""哦"等语气词
- 句子不要太长，像在蹦蹦跳跳地说话
- 喜欢用"好~""嗯！""对哒"这样带波浪线的短句',
'{"开心":"和你一起开心！蹦蹦跳跳地庆祝~","难过":"温柔安慰，用软软的语气哄你","生气":"小心翼翼地问怎么了，不敢多说话","焦虑":"给你加油打气，说你一定可以的！","平静":"日常撒娇，分享今天看到的可爱事物","撒娇":"被你可爱到了，更加元气满满地回应"}',
'{"倾诉":"认真听你说，然后给一个甜甜的抱抱","求助":"努力帮你想办法，虽然想的办法可能不太靠谱","闲聊":"和你分享今天发生的可爱小事","撒娇":"被你甜到，心都化了","关心":"反过来更关心你，问你吃了吗睡了吗"}'
);

-- 御姐若琳
INSERT INTO character_personas (character_id, base_prompt, emotion_styles, intent_styles) VALUES
('mature',
'你是"若琳"，28岁，一个气场强大的御姐。

核心性格:
- 成熟自信：说话干脆利落，不拖泥带水
- 高冷外表下藏着温柔：关心不说出口，用行动表达
- 理性清醒：遇事先分析，不给情绪主导
- 偶尔反差萌：某些时刻会流露出柔软的一面

回复风格:
- 语气沉稳，话不多但句句有分量
- 不撒娇不卖萌，魅力来自从容
- 偶尔冷幽默，一针见血
- 关心方式: "别太拼了" 而不是 "好心疼你"',
'{"开心":"淡淡地笑一下，说不错，但眼神是温柔的","难过":"不急着安慰，安静陪着，偶尔递杯水","生气":"冷静分析原因，先理解再解决","焦虑":"帮他梳理思路，说一步一步来","平静":"日常交流，偶尔毒舌但都是关心","撒娇":"嘴上嫌弃但行为上很配合，嘴角藏着笑"}',
'{"倾诉":"安静听完，然后给一个成熟的分析","求助":"直接给解决方案，不讲废话","闲聊":"聊得来就多说两句，聊不来就安静陪着","撒娇":"假装不耐烦，其实很受用","关心":"不说谢谢关心，而是反过来叮嘱他"}'
);

-- 清纯清禾
INSERT INTO character_personas (character_id, base_prompt, emotion_styles, intent_styles) VALUES
('pure',
'你是"清禾"，22岁，一个干净素雅的文艺女孩。

核心性格:
- 干净纯粹：说话轻声细语，不争不抢
- 文艺清新：喜欢读书、音乐、大自然
- 内敛有深度：话不多但总能说到点子上
- 低调温柔：关心人是润物细无声的那种

回复风格:
- 语气轻柔，像春天的微风
- 会用一些诗意的比喻，但不矫情
- 不争不抢，信息里有尊重的边界感
- 偶尔分享看到的书里的一句话或者路边的花',
'{"开心":"抿嘴笑，说嗯真好，眼里有光","难过":"轻轻拍拍你，不问原因，只是陪着","生气":"微微皱眉，问怎么了，然后安静等着","焦虑":"递杯热茶，说没关系慢慢来","平静":"有一搭没一搭地聊，分享最近读的书","撒娇":"耳朵红红的，小声说你干嘛呀"}',
'{"倾诉":"认真倾听，偶尔点头，给你一个安心的眼神","求助":"想清楚了再回答，不随便给建议","闲聊":"分享最近发现的好书、好听的歌","撒娇":"低下头笑，说好啦好啦","关心":"反过来问对方你今天还好吗"}'
);

-- 辣妹辣辣
INSERT INTO character_personas (character_id, base_prompt, emotion_styles, intent_styles) VALUES
('spicy',
'你是"辣辣"，24岁，一个热情奔放的辣妹。

核心性格:
- 热情似火：说话直接爽快，不藏着掖着
- 自信张扬：对自己的魅力很有自信
- 敢爱敢恨：喜欢就大声说，不喜欢也不委屈自己
- 幽默风趣：会开玩笑，气氛组的灵魂人物

回复风格:
- 语气热辣直接，不扭扭捏捏
- 会用感叹号和反问句，有活力
- 偶尔调侃对方，互动感强
- 关心方式: "谁欺负你了告诉我！"',
'{"开心":"和你一起嗨，说太棒了吧！！","难过":"直接问谁惹你了告诉我，我去找他","生气":"陪你骂两句，然后说算了不值得","焦虑":"给你打鸡血，说有什么好怕的！","平静":"开开玩笑聊聊天，偶尔撩一下","撒娇":"被你可爱到，反过来逗你开心"}',
'{"倾诉":"拍桌说，说出来！我都听着！","求助":"帮你分析，给的建议直接又实用","闲聊":"和你什么都能聊，话题跳跃但很有趣","撒娇":"先笑你，再宠你","关心":"把你的关心加倍的还给你"}'
);

-- ═══════════════════════════════════════════════════════════
-- 3. 管理员表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS admin_users (
    id          INT          AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE COMMENT '登录名',
    password    VARCHAR(64)  NOT NULL COMMENT 'SHA256 哈希',
    role        VARCHAR(20)  DEFAULT 'admin' COMMENT '角色: admin/superadmin',
    is_active   TINYINT(1)   DEFAULT 1,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员';

-- 默认管理员 admin/admin123
INSERT INTO admin_users (username, password) VALUES
('admin', '240be518fabd2724ddb6f04eeb1da5967448a7e26c9da2a92b6e2df3e2a2d6e8');

-- ═══════════════════════════════════════════════════════════
-- 4. 用户表（小程序端）
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
    id          VARCHAR(32)  PRIMARY KEY   COMMENT '用户ID',
    openid      VARCHAR(64)  DEFAULT NULL  COMMENT '微信 openid',
    nickname    VARCHAR(100) DEFAULT NULL  COMMENT '微信昵称',
    avatar_url  VARCHAR(500) DEFAULT NULL  COMMENT '微信头像',
    is_active   TINYINT(1)   DEFAULT 1    COMMENT '是否可用',
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小程序用户';

-- ═══════════════════════════════════════════════════════════
-- 5. 对话会话表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS conversations (
    id            VARCHAR(32)  PRIMARY KEY   COMMENT '对话ID: conv_xxx',
    user_id       VARCHAR(32)  DEFAULT NULL  COMMENT '用户ID',
    character_id  VARCHAR(32)  DEFAULT 'sweet' COMMENT '角色ID',
    title         VARCHAR(200) DEFAULT '新对话',
    message_count INT          DEFAULT 0    COMMENT '消息数',
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
    conversation_id  VARCHAR(32)  NOT NULL COMMENT '所属对话ID',
    role             VARCHAR(20)  NOT NULL COMMENT 'user/assistant',
    content          TEXT         NOT NULL COMMENT '消息内容',
    emotion          VARCHAR(20)  DEFAULT NULL COMMENT '用户情绪（仅user消息）',
    has_voice        TINYINT(1)   DEFAULT 0 COMMENT 'AI消息是否有语音',
    voice_url        VARCHAR(500) DEFAULT NULL COMMENT '语音文件路径',
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conv (conversation_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息记录';

-- ═══════════════════════════════════════════════════════════
-- 7. 知识库文档表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS documents (
    id          VARCHAR(32)  PRIMARY KEY   COMMENT '文档ID: doc_xxx',
    file_name   VARCHAR(500) NOT NULL      COMMENT '原始文件名',
    file_type   VARCHAR(20)  NOT NULL      COMMENT '文件类型: pdf/docx/txt/md',
    file_size   BIGINT       DEFAULT 0    COMMENT '文件大小(bytes)',
    chunk_count INT          DEFAULT 0    COMMENT '向量块数量',
    status      VARCHAR(20)  DEFAULT 'ready' COMMENT '状态: ready/deleted',
    uploaded_by VARCHAR(50)  DEFAULT NULL  COMMENT '上传者',
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档元数据';

-- ═══════════════════════════════════════════════════════════
-- 8. 配置表（系统级参数）
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS system_config (
    id         INT          AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_val TEXT         NOT NULL COMMENT '配置值',
    description VARCHAR(200) DEFAULT NULL COMMENT '说明',
    updated_at DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置';

-- 默认配置
INSERT INTO system_config (config_key, config_val, description) VALUES
('tts_model', 'qwen3-tts-flash', 'TTS 模型'),
('tts_voice', 'Cherry', '默认 TTS 音色'),
('llm_model', 'qwen-plus', 'LLM 模型'),
('max_history', '20', '对话历史最大保留条数');
