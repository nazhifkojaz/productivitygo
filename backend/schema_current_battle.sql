-- Add current_battle column to profiles table to track active/completed battle state
ALTER TABLE profiles 
ADD COLUMN current_battle UUID REFERENCES battles(id);

-- Create an index for faster lookups
CREATE INDEX idx_profiles_current_battle ON profiles(current_battle);
