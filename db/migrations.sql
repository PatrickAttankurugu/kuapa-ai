-- Kuapa AI Database Schema
-- PostgreSQL + pgVector for agricultural advisory system

-- Enable pgVector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    preferred_language VARCHAR(5) DEFAULT 'en',
    location VARCHAR(255),
    farm_size VARCHAR(50),
    crops TEXT[], -- Array of crops they grow
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create messages table with pgVector for embeddings
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL, -- 'text', 'voice', 'system'
    direction VARCHAR(10) NOT NULL, -- 'incoming', 'outgoing'
    content TEXT NOT NULL,
    transcribed_text TEXT, -- For voice messages
    language VARCHAR(5),
    audio_file_path TEXT, -- Path to stored audio file
    embedding vector(768), -- For semantic search (Gemini embeddings are 768 dimensions)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create sessions table for tracking active WhatsApp sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    receive_notifications BOOLEAN DEFAULT TRUE,
    notification_time TIME,
    topics_of_interest TEXT[],
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create analytics table for tracking usage
CREATE TABLE IF NOT EXISTS analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active, last_active_at);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type, direction);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics(user_id, event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_created ON analytics(created_at);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_messages_embedding ON messages USING ivfflat (embedding vector_cosine_ops);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to get user's recent conversations
CREATE OR REPLACE FUNCTION get_user_recent_conversations(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    conversation_id UUID,
    started_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER,
    last_message TEXT,
    last_message_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS conversation_id,
        c.started_at,
        c.message_count,
        m.content AS last_message,
        m.created_at AS last_message_at
    FROM conversations c
    LEFT JOIN LATERAL (
        SELECT content, created_at
        FROM messages
        WHERE conversation_id = c.id
        ORDER BY created_at DESC
        LIMIT 1
    ) m ON true
    WHERE c.user_id = p_user_id
    ORDER BY c.started_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Create function to search messages by embedding similarity
CREATE OR REPLACE FUNCTION search_similar_messages(
    p_embedding vector(768),
    p_user_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    message_id UUID,
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id AS message_id,
        m.content,
        1 - (m.embedding <=> p_embedding) AS similarity
    FROM messages m
    WHERE m.embedding IS NOT NULL
        AND (p_user_id IS NULL OR m.user_id = p_user_id)
    ORDER BY m.embedding <=> p_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Insert default system user for automated messages
INSERT INTO users (id, phone_number, name, preferred_language)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system',
    'Kuapa AI System',
    'en'
) ON CONFLICT (phone_number) DO NOTHING;

-- Create view for active user stats
CREATE OR REPLACE VIEW active_user_stats AS
SELECT 
    COUNT(DISTINCT u.id) AS total_users,
    COUNT(DISTINCT CASE WHEN u.last_active_at > NOW() - INTERVAL '24 hours' THEN u.id END) AS active_last_24h,
    COUNT(DISTINCT CASE WHEN u.last_active_at > NOW() - INTERVAL '7 days' THEN u.id END) AS active_last_7d,
    COUNT(DISTINCT CASE WHEN u.last_active_at > NOW() - INTERVAL '30 days' THEN u.id END) AS active_last_30d,
    COUNT(DISTINCT c.id) AS total_conversations,
    COUNT(m.id) AS total_messages,
    COUNT(CASE WHEN m.message_type = 'voice' THEN 1 END) AS voice_messages,
    COUNT(CASE WHEN m.message_type = 'text' THEN 1 END) AS text_messages
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN messages m ON u.id = m.user_id
WHERE u.phone_number != 'system';

-- Grant permissions (adjust based on your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kuapa_ai_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kuapa_ai_user;

COMMIT;
