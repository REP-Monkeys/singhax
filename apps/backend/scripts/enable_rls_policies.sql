-- Enable Row Level Security (RLS) policies for Supabase Auth integration
-- This script enables RLS on all tables and creates policies that allow
-- users to access only their own data using auth.uid()

-- ============================================================================
-- USERS TABLE
-- ============================================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can view their own record
CREATE POLICY "users_select_own" 
ON users FOR SELECT 
TO authenticated
USING (id = auth.uid());

-- Users can update their own record
CREATE POLICY "users_update_own" 
ON users FOR UPDATE 
TO authenticated
USING (id = auth.uid())
WITH CHECK (id = auth.uid());

-- Service role can do everything (for backend operations)
CREATE POLICY "users_service_role_all"
ON users FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- TRIPS TABLE
-- ============================================================================
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;

-- Users can view their own trips
CREATE POLICY "trips_select_own" 
ON trips FOR SELECT 
TO authenticated
USING (user_id = auth.uid());

-- Users can insert their own trips
CREATE POLICY "trips_insert_own" 
ON trips FOR INSERT 
TO authenticated
WITH CHECK (user_id = auth.uid());

-- Users can update their own trips
CREATE POLICY "trips_update_own" 
ON trips FOR UPDATE 
TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Users can delete their own trips
CREATE POLICY "trips_delete_own" 
ON trips FOR DELETE 
TO authenticated
USING (user_id = auth.uid());

-- Service role can do everything
CREATE POLICY "trips_service_role_all"
ON trips FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- QUOTES TABLE
-- ============================================================================
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;

-- Users can view their own quotes
CREATE POLICY "quotes_select_own" 
ON quotes FOR SELECT 
TO authenticated
USING (user_id = auth.uid());

-- Users can insert their own quotes
CREATE POLICY "quotes_insert_own" 
ON quotes FOR INSERT 
TO authenticated
WITH CHECK (user_id = auth.uid());

-- Users can update their own quotes
CREATE POLICY "quotes_update_own" 
ON quotes FOR UPDATE 
TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Users can delete their own quotes
CREATE POLICY "quotes_delete_own" 
ON quotes FOR DELETE 
TO authenticated
USING (user_id = auth.uid());

-- Service role can do everything
CREATE POLICY "quotes_service_role_all"
ON quotes FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- POLICIES TABLE
-- ============================================================================
ALTER TABLE policies ENABLE ROW LEVEL SECURITY;

-- Users can view their own policies
CREATE POLICY "policies_select_own" 
ON policies FOR SELECT 
TO authenticated
USING (user_id = auth.uid());

-- Users can insert their own policies (usually created via backend)
CREATE POLICY "policies_insert_own" 
ON policies FOR INSERT 
TO authenticated
WITH CHECK (user_id = auth.uid());

-- Users can update their own policies (limited - status updates mainly)
CREATE POLICY "policies_update_own" 
ON policies FOR UPDATE 
TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Service role can do everything
CREATE POLICY "policies_service_role_all"
ON policies FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- CLAIMS TABLE (accessed via policies)
-- ============================================================================
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;

-- Users can view claims for their own policies
CREATE POLICY "claims_select_own" 
ON claims FOR SELECT 
TO authenticated
USING (
    policy_id IN (
        SELECT id FROM policies WHERE user_id = auth.uid()
    )
);

-- Users can insert claims for their own policies
CREATE POLICY "claims_insert_own" 
ON claims FOR INSERT 
TO authenticated
WITH CHECK (
    policy_id IN (
        SELECT id FROM policies WHERE user_id = auth.uid()
    )
);

-- Users can update claims for their own policies
CREATE POLICY "claims_update_own" 
ON claims FOR UPDATE 
TO authenticated
USING (
    policy_id IN (
        SELECT id FROM policies WHERE user_id = auth.uid()
    )
)
WITH CHECK (
    policy_id IN (
        SELECT id FROM policies WHERE user_id = auth.uid()
    )
);

-- Service role can do everything
CREATE POLICY "claims_service_role_all"
ON claims FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- TRAVELERS TABLE
-- ============================================================================
ALTER TABLE travelers ENABLE ROW LEVEL SECURITY;

-- Users can view their own travelers
CREATE POLICY "travelers_select_own" 
ON travelers FOR SELECT 
TO authenticated
USING (user_id = auth.uid());

-- Users can insert their own travelers
CREATE POLICY "travelers_insert_own" 
ON travelers FOR INSERT 
TO authenticated
WITH CHECK (user_id = auth.uid());

-- Users can update their own travelers
CREATE POLICY "travelers_update_own" 
ON travelers FOR UPDATE 
TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Users can delete their own travelers
CREATE POLICY "travelers_delete_own" 
ON travelers FOR DELETE 
TO authenticated
USING (user_id = auth.uid());

-- Service role can do everything
CREATE POLICY "travelers_service_role_all"
ON travelers FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- CHAT_HISTORY TABLE
-- ============================================================================
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Users can view their own chat history
CREATE POLICY "chat_history_select_own" 
ON chat_history FOR SELECT 
TO authenticated
USING (user_id = auth.uid());

-- Users can insert their own chat history
CREATE POLICY "chat_history_insert_own" 
ON chat_history FOR INSERT 
TO authenticated
WITH CHECK (user_id = auth.uid());

-- Users typically don't update chat history, but allow it
CREATE POLICY "chat_history_update_own" 
ON chat_history FOR UPDATE 
TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Users can delete their own chat history
CREATE POLICY "chat_history_delete_own" 
ON chat_history FOR DELETE 
TO authenticated
USING (user_id = auth.uid());

-- Service role can do everything
CREATE POLICY "chat_history_service_role_all"
ON chat_history FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- AUDIT_LOG TABLE (special handling - users view own, service can insert)
-- ============================================================================
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Users can view their own audit logs
CREATE POLICY "audit_log_select_own" 
ON audit_log FOR SELECT 
TO authenticated
USING (user_id = auth.uid() OR user_id IS NULL);

-- Service role can insert audit logs
CREATE POLICY "audit_log_insert_service" 
ON audit_log FOR INSERT 
TO service_role
WITH CHECK (true);

-- Service role can view all audit logs
CREATE POLICY "audit_log_service_role_all"
ON audit_log FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- RAG_DOCUMENTS TABLE (read-only for authenticated users, admin-only write)
-- ============================================================================
ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY;

-- All authenticated users can read RAG documents
CREATE POLICY "rag_documents_select_authenticated" 
ON rag_documents FOR SELECT 
TO authenticated
USING (true);

-- Only service role can insert/update/delete RAG documents
CREATE POLICY "rag_documents_service_role_all"
ON rag_documents FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. To apply these policies, run this script in your Supabase SQL editor
-- 2. Make sure all user IDs in your tables match Supabase auth.users.id
-- 3. The service_role policies allow your backend (with service role key) to bypass RLS
-- 4. For production, consider more granular policies based on your needs
-- 5. Test these policies thoroughly before deploying to production

