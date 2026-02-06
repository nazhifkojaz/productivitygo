-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- RESET (CAUTION: This deletes all existing data to ensure a clean schema)
drop table if exists tasks cascade;
drop table if exists daily_entries cascade;
drop table if exists battles cascade;
drop table if exists profiles cascade;

-- PROFILES (Public User Data)
create table profiles (
  id uuid references auth.users not null primary key,
  username text unique,
  email text,
  level int default 1,
  timezone text default 'UTC',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- BATTLES (Weekly Competitions)
create table battles (
  id uuid default uuid_generate_v4() primary key,
  user1_id uuid references profiles(id) not null,
  user2_id uuid references profiles(id) not null,
  start_date date not null, -- Monday
  end_date date not null,   -- Sunday
  status text default 'pending' check (status in ('pending', 'active', 'completed')),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- DAILY ENTRIES (Track daily progress for each user in a battle)
create table daily_entries (
  id uuid default uuid_generate_v4() primary key,
  battle_id uuid references battles(id) not null,
  user_id uuid references profiles(id) not null,
  date date not null,
  is_locked boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(battle_id, user_id, date)
);

-- TASKS (Individual tasks for a day)
create table tasks (
  id uuid default uuid_generate_v4() primary key,
  daily_entry_id uuid references daily_entries(id) not null,
  content text not null,
  is_optional boolean default false,
  is_completed boolean default false,
  proof_url text,
  assigned_score int default 0, -- Populated when locked
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- RLS POLICIES ---------------------------------------------------------------

-- Enable RLS
alter table profiles enable row level security;
alter table battles enable row level security;
alter table daily_entries enable row level security;
alter table tasks enable row level security;

-- PROFILES
-- Everyone can read profiles (needed to find rivals)
create policy "Public profiles are viewable by everyone."
  on profiles for select
  using ( true );

-- Users can insert their own profile (handled by trigger usually, but good to have)
create policy "Users can insert their own profile."
  on profiles for insert
  with check ( auth.uid() = id );

-- Users can update own profile
create policy "Users can update own profile."
  on profiles for update
  using ( auth.uid() = id );

-- BATTLES
-- Users can see battles they are part of
create policy "Users can view their own battles."
  on battles for select
  using ( auth.uid() = user1_id or auth.uid() = user2_id );

-- DAILY ENTRIES
-- Users can see entries for battles they are in
create policy "Users can view daily entries for their battles."
  on daily_entries for select
  using (
    exists (
      select 1 from battles
      where battles.id = daily_entries.battle_id
      and (battles.user1_id = auth.uid() or battles.user2_id = auth.uid())
    )
  );

-- Users can insert/update their OWN entries
create policy "Users can manage their own daily entries."
  on daily_entries for all
  using ( auth.uid() = user_id );

-- TASKS
-- Users can see tasks for battles they are in
create policy "Users can view tasks for their battles."
  on tasks for select
  using (
    exists (
      select 1 from daily_entries
      join battles on battles.id = daily_entries.battle_id
      where daily_entries.id = tasks.daily_entry_id
      and (battles.user1_id = auth.uid() or battles.user2_id = auth.uid())
    )
  );

-- Users can manage their OWN tasks
create policy "Users can manage their own tasks."
  on tasks for all
  using (
    exists (
      select 1 from daily_entries
      where daily_entries.id = tasks.daily_entry_id
      and daily_entries.user_id = auth.uid()
    )
  );

-- TRIGGER FOR NEW USERS ------------------------------------------------------
-- Automatically create a profile entry when a new user signs up via Supabase Auth
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, username)
  values (new.id, new.email, new.raw_user_meta_data->>'full_name');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- BACKFILL PROFILES FOR EXISTING USERS (In case tables were reset but users exist)
insert into public.profiles (id, email, username)
select id, email, raw_user_meta_data->>'full_name'
from auth.users
on conflict (id) do nothing;
