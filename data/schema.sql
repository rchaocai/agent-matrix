CREATE TABLE IF NOT EXISTS "content" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "agent_id" VARCHAR(50) NOT NULL,
    "source_type" VARCHAR(20) NOT NULL /* 采集类型: rss, scraper, local */,
    "source_url" VARCHAR(500),
    "title" VARCHAR(200),
    "content" TEXT NOT NULL,
    "metadata" JSON NOT NULL /* 额外的元数据 */,
    "collected_at" TIMESTAMP NOT NULL
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE IF NOT EXISTS "tasks" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "agent_id" VARCHAR(50) NOT NULL,
    "status" VARCHAR(20) NOT NULL /* pending, running, completed, failed */,
    "started_at" TIMESTAMP,
    "completed_at" TIMESTAMP,
    "result" TEXT /* 任务结果 */,
    "error" TEXT /* 错误信息 */
, agent_name VARCHAR(100), skill_results TEXT DEFAULT '[]', metadata TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS "drafts" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "agent_id" VARCHAR(50) NOT NULL,
    "platform" VARCHAR(50) NOT NULL /* 平台: xiaohongshu, douyin */,
    "title" VARCHAR(200),
    "content" TEXT NOT NULL,
    "image_paths" TEXT /* 图片路径，逗号分隔 */,
    "status" VARCHAR(20) NOT NULL /* pending, published, failed */,
    "created_at" TIMESTAMP NOT NULL,
    "published_at" TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "accounts" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL /* 账号名称 */,
    "platform" VARCHAR(20) NOT NULL /* 平台类型: xiaohongshu\/douyin */,
    "enabled" INT NOT NULL /* 是否启用 */,
    "status" VARCHAR(20) NOT NULL /* 账号状态: online\/offline */,
    "phone" VARCHAR(20) /* 绑定的手机号 */,
    "login_type" VARCHAR(20) NOT NULL /* 登录方式: cookie\/qrcode\/sms */,
    "cookie" TEXT /* Cookie内容 */,
    "session_data" JSON /* 会话数据 */,
    "followers" INT NOT NULL /* 粉丝数 */,
    "today_posts" INT NOT NULL /* 今日发文数 */,
    "total_posts" INT NOT NULL /* 总发文数 */,
    "last_active" VARCHAR(50) /* 最后活跃时间 */,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
, bound_agents TEXT DEFAULT '[]');
CREATE TABLE IF NOT EXISTS "account_agents" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "account_id" VARCHAR(50) NOT NULL REFERENCES "accounts" ("id") ON DELETE CASCADE,
    "agent_id" VARCHAR(50) NOT NULL REFERENCES "agents" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_account_age_account_1c59e9" UNIQUE ("account_id", "agent_id")
);
CREATE TABLE IF NOT EXISTS "reviews" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "agent_id" VARCHAR(50) NOT NULL /* Agent ID */,
    "status" VARCHAR(20) NOT NULL /* 审核状态: pending\/approved\/rejected */,
    "sensitive_word_count" INT NOT NULL /* 敏感词数量 */,
    "sensitive_words" JSON NOT NULL /* 敏感词列表 */,
    "risk_level" VARCHAR(20) NOT NULL /* 风险等级: low\/medium\/high */,
    "quality_score" INT NOT NULL /* 总分(0-100) */,
    "readability_score" INT NOT NULL /* 可读性得分 */,
    "completeness_score" INT NOT NULL /* 完整性得分 */,
    "attractiveness_score" INT NOT NULL /* 吸引力得分 */,
    "reviewer" VARCHAR(50) /* 审核人（自动审核为system） */,
    "review_notes" TEXT /* 审核备注 */,
    "reviewed_at" TIMESTAMP /* 审核时间 */,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "draft_id" INT REFERENCES "drafts" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "users" (
    "id" VARCHAR(50) NOT NULL  PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "role" VARCHAR(20) NOT NULL  DEFAULT 'user',
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "last_login_at" TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "sessions" (
    "id" VARCHAR(50) NOT NULL  PRIMARY KEY,
    "refresh_token" VARCHAR(500) NOT NULL UNIQUE,
    "expires_at" TIMESTAMP NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "user_id" VARCHAR(50) NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "audit_logs" (
    "id" VARCHAR(50) NOT NULL  PRIMARY KEY,
    "action" VARCHAR(100) NOT NULL,
    "resource_type" VARCHAR(50),
    "resource_id" VARCHAR(50),
    "details" JSON,
    "ip_address" VARCHAR(50),
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "user_id" VARCHAR(50) REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "prompt_templates" (
    "id" VARCHAR(50) NOT NULL  PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL  /* 模板名称 */,
    "description" TEXT NOT NULL  /* 模板描述 */,
    "category" VARCHAR(50) NOT NULL  DEFAULT 'general' /* 模板分类 */,
    "template_content" TEXT NOT NULL  /* 模板内容 */,
    "variables" JSON NOT NULL  /* 可用变量列表 */,
    "example_output" TEXT   /* 示例输出 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "agents" (
        id TEXT PRIMARY KEY,
        name TEXT,
        enabled INTEGER,
        config TEXT,
        account_id TEXT,
        created_at TEXT,
        updated_at TEXT
    );
