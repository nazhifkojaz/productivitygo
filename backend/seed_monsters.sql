-- ============================================================================
-- Adventure Mode: Monster Data Seeding
-- ============================================================================
-- Inserts 42 monsters across 5 tiers for Adventure Mode.
-- Run this AFTER creating the monsters table (schema_monsters.sql)
-- ============================================================================

-- Clear existing monsters (for idempotent re-seeding)
DELETE FROM monsters;

-- Insert all 42 monsters
INSERT INTO monsters (name, emoji, tier, base_hp, description) VALUES
  -- Tier 1: Easy (100-200 HP) - 10 monsters
  ('Lazy Slime', '🟢', 'easy', 100, 'Just five more minutes...'),
  ('Snooze Sprite', '😴', 'easy', 110, 'Whispers "tomorrow is fine"'),
  ('Distraction Rat', '🐀', 'easy', 120, 'Scurries through your focus'),
  ('Excuse Imp', '👿', 'easy', 130, 'Always has a reason not to'),
  ('Scroll Goblin', '📱', 'easy', 140, 'Have you seen this meme?'),
  ('Couch Potato', '🥔', 'easy', 150, 'The gravity is strong with this one'),
  ('Notification Gremlin', '🔔', 'easy', 160, '*ding* *ding* *ding*'),
  ('I''ll Do It Later Larry', '🦥', 'easy', 180, 'Tomorrow''s problem, amirite?'),
  ('The Snack Siren', '🍕', 'easy', 190, 'Psst... the fridge is calling'),
  ('WiFi Vampire', '📶', 'easy', 200, 'Drains your time, not your blood'),

  -- Tier 2: Medium (200-320 HP) - 10 monsters
  ('Procrastination Goblin', '👺', 'medium', 200, 'There''s still time...'),
  ('Netflix Naga', '🐍', 'medium', 220, 'Just one more episode... or season'),
  ('Comfort Zone Troll', '🧌', 'medium', 240, 'Why leave? It''s cozy here'),
  ('Doom Scroller', '👁️', 'medium', 250, 'Infinite content, zero productivity'),
  ('Snack Attack Wolf', '🐺', 'medium', 260, 'Hungry for your time (and snacks)'),
  ('YouTube Rabbit', '🐰', 'medium', 270, 'Recommended for you is its weapon'),
  ('Bed Gravity Bear', '🐻', 'medium', 280, 'Makes your bed extra magnetic'),
  ('Reply Guy Wraith', '💬', 'medium', 290, 'Well, actually...'),
  ('Tabocalypse', '🗂️', 'medium', 300, '47 open tabs and counting'),
  ('The Benchwarmer', '🪑', 'medium', 320, 'Just warming up... indefinitely'),

  -- Tier 3: Hard (320-450 HP) - 10 monsters
  ('Burnout Specter', '👻', 'hard', 320, 'Drains energy you didn''t know you had'),
  ('Impostor Shade', '🎭', 'hard', 340, 'You''re faking it. Everyone knows.'),
  ('FOMO Phantom', '💨', 'hard', 360, 'Everyone''s having fun without you'),
  ('Perfectionism Knight', '⚔️', 'hard', 380, 'Nothing is ever good enough'),
  ('Analysis Paralysis', '🤯', 'hard', 390, '47 pros/cons lists later...'),
  ('Scope Creep', '🦎', 'hard', 400, 'While you''re at it, could you also...'),
  ('Meeting Minotaur', '📅', 'hard', 410, 'This could''ve been an email'),
  ('Decision Fatigue Demon', '🎰', 'hard', 420, 'What should I do? What SHOULD I do??'),
  ('The Comparer', '👀', 'hard', 430, 'Their highlight reel vs your behind-the-scenes'),
  ('Sunk Cost Succubus', '💸', 'hard', 450, 'But I''ve already invested so much...'),

  -- Tier 4: Expert (450-550 HP) - 7 monsters
  ('Anxiety Dragon', '🐲', 'expert', 450, 'What if everything goes wrong? What if??'),
  ('Overwhelm Hydra', '🐉', 'expert', 470, 'Cut one task, two more appear'),
  ('Comparison Demon', '😈', 'expert', 490, 'They''re your age and already...'),
  ('The Infinite Backlog', '📚', 'expert', 500, 'It only grows. It never shrinks.'),
  ('Email Avalanche', '📧', 'expert', 510, '1,247 unread and counting'),
  ('Context Switch Chimera', '🦁', 'expert', 530, 'Three heads, three tasks, zero focus'),
  ('Imposter Syndrome Supreme', '👑', 'expert', 550, 'The final form of self-doubt'),

  -- Tier 5: Boss (550-700 HP) - 5 monsters
  ('The Void of Inaction', '🕳️', 'boss', 550, 'Where motivation goes to die'),
  ('Chaos Titan', '🔥', 'boss', 600, 'Master of disorder and delay'),
  ('The Procrastinator King', '👑', 'boss', 650, 'I''ll defeat you... eventually'),
  ('Existential Dread Lord', '🌑', 'boss', 680, 'Does any of this even matter?'),
  ('Burnout Phoenix', '🔴', 'boss', 700, 'Rises from the ashes of your motivation')
ON CONFLICT (id) DO NOTHING;

-- Verification query (run to confirm seeding)
-- SELECT tier, COUNT(*) as count, MIN(base_hp) as min_hp, MAX(base_hp) as max_hp
-- FROM monsters
-- GROUP BY tier
-- ORDER BY min_hp;
-- Expected: easy=10, medium=10, hard=10, expert=7, boss=5
