-- Music generations metadata
CREATE TABLE IF NOT EXISTS music_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    use_case VARCHAR(20) NOT NULL CHECK (use_case IN ('marketing', 'show')),
    model_name VARCHAR(50) NOT NULL,
    genre VARCHAR(100),
    mood VARCHAR(100),
    tempo INTEGER,
    key_signature VARCHAR(10),
    duration_seconds INTEGER NOT NULL,
    minio_key TEXT NOT NULL,
    format VARCHAR(10) NOT NULL DEFAULT 'mp3',
    file_size_bytes INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approval_status VARCHAR(20),
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_at TIMESTAMPTZ,
    cache_hit_count INTEGER DEFAULT 0,
    last_cached_at TIMESTAMPTZ
);

CREATE INDEX idx_music_prompt_hash ON music_generations(prompt_hash);
CREATE INDEX idx_music_status ON music_generations(status);
CREATE INDEX idx_music_approval ON music_generations(approval_status) WHERE approval_status IS NOT NULL;
CREATE INDEX idx_music_created_at ON music_generations(created_at DESC);

-- Approval audit trail
CREATE TABLE IF NOT EXISTS music_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    music_id UUID NOT NULL REFERENCES music_generations(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    user_id UUID NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_timestamp ON music_approvals(created_at DESC);

-- Usage tracking
CREATE TABLE IF NOT EXISTS music_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    music_id UUID,
    was_cache_hit BOOLEAN NOT NULL,
    generation_duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usage_timestamp ON music_usage_log(created_at DESC);
