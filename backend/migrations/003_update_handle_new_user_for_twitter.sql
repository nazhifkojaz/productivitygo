-- ============================================================================
-- Migration 003: Update handle_new_user Trigger for Twitter OAuth
-- ============================================================================
-- This migration updates the auto-profile-creation trigger to:
--   1. Support Twitter/X OAuth (uses 'user_name' instead of 'full_name')
--   2. Handle username conflicts with numbered suffixes
--   3. Add fallback to email prefix
--
-- Run this in Supabase SQL Editor for production deployment.
-- ============================================================================

-- Drop existing trigger and recreate function
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  base_username TEXT;
  final_username TEXT;
  counter INT := 1;
BEGIN
  -- Try Twitter's user_name first, then Google's full_name, then email prefix
  base_username := COALESCE(
    new.raw_user_meta_data->>'user_name',   -- Twitter/X
    new.raw_user_meta_data->>'full_name',   -- Google
    SPLIT_PART(new.email, '@', 1)           -- Fallback to email prefix
  );

  final_username := base_username;

  -- Append number if username already exists
  WHILE EXISTS (SELECT 1 FROM profiles WHERE username = final_username) LOOP
    counter := counter + 1;
    final_username := base_username || counter;
  END LOOP;

  INSERT INTO public.profiles (id, email, username)
  VALUES (new.id, new.email, final_username);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Recreate trigger
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
