-- Create a table to store the OpenAI Thread Objects
create table
  thread_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    object text check (object in ('thread')),
    created_at bigint default extract(epoch FROM NOW()) NOT NULL,
    tool_resources jsonb,
    metadata jsonb
  );

-- Create a table to store the OpenAI Message Objects
create table
  message_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    object text check (object in ('thread.message')),
    created_at bigint default extract(epoch FROM NOW()) NOT NULL,
    thread_id uuid,
    status text,
    incomplete_details jsonb,
    completed_at bigint,
    incomplete_at bigint,
    role text,
    content jsonb,
    assistant_id uuid, -- No foreign key constraint, can be null and doesn't have to refer to an assistant that exists
    run_id uuid, -- No foreign key constraint, can be null and doesn't have to refer to a thread that exists
    attachments jsonb,
    metadata jsonb
  );

-- Create a table to store the OpenAI Run Objects
create table
  run_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    object text check (object in ('thread.run')),
    created_at bigint default extract(epoch FROM NOW()) NOT NULL,
    thread_id uuid,
    assistant_id uuid,
    status text,
    required_action jsonb,
    last_error jsonb,
    expires_at bigint,
    started_at bigint,
    cancelled_at bigint,
    failed_at bigint,
    completed_at bigint,
    model text,
    instructions text,
    tools jsonb,
    metadata jsonb,
    stream boolean,
    file_ids uuid[],
    incomplete_details jsonb,
    usage jsonb,
    temperature float,
    top_p float,
    max_prompt_tokens int,
    max_completion_tokens int,
    truncation_strategy jsonb,
    tool_choice jsonb,
    response_format jsonb
  );

-- Create a table to store the OpenAI Run Step Objects
create table
  run_step_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    object text check (object in ('thread.run.step')),
    created_at bigint default extract(epoch FROM NOW()) NOT NULL,
    assistant_id uuid,
    thread_id uuid,
    run_id uuid,
    step_type text,
    status text,
    step_details jsonb,
    last_error jsonb,
    expired_at bigint,
    cancelled_at bigint,
    failed_at bigint,
    completed_at bigint,
    metadata jsonb,
    usage jsonb
  );

-- Foreign key constraints for message_objects
alter table message_objects add constraint fk_message_objects_thread_objects
    foreign key (thread_id)
    REFERENCES thread_objects (id)
    ON DELETE CASCADE;

-- Foreign key constraints for run_objects
alter table run_objects add constraint fk_run_objects_thread_objects
    foreign key (thread_id)
    REFERENCES thread_objects (id);
alter table run_objects add constraint fk_run_objects_assistant_objects
    foreign key (assistant_id)
    REFERENCES assistant_objects (id);

-- Foreign key constraints for run_step_objects
alter table run_step_objects add constraint fk_run_step_objects_thread_objects
    foreign key (thread_id)
    REFERENCES thread_objects (id);
alter table run_step_objects add constraint fk_run_step_objects_assistant_objects
    foreign key (assistant_id)
    REFERENCES assistant_objects (id);
alter table run_step_objects add constraint fk_run_step_objects_run_objects
    foreign key (run_id)
    REFERENCES run_objects (id);

-- RLS policies
alter table thread_objects enable row level security;
alter table message_objects enable row level security;
alter table run_objects enable row level security;
alter table run_step_objects enable row level security;

-- Policies for thread_objects
create policy "Individuals can view their own thread_objects." on thread_objects for
    select using (auth.uid() = user_id);
create policy "Individuals can create thread_objects." on thread_objects for
    insert with check (auth.uid() = user_id);
create policy "Individuals can update their own thread_objects." on thread_objects for
    update using (auth.uid() = user_id);
create policy "Individuals can delete their own thread_objects." on thread_objects for
    delete using (auth.uid() = user_id);

-- Policies for message_objects
create policy "Individuals can view their own message_objects." on message_objects for
    select using (auth.uid() = user_id);
create policy "Individuals can create message_objects." on message_objects for
    insert with check (auth.uid() = user_id);
create policy "Individuals can update their own message_objects." on message_objects for
    update using (auth.uid() = user_id);
create policy "Individuals can delete their own message_objects." on message_objects for
    delete using (auth.uid() = user_id);

-- Policies for run_objects
create policy "Individuals can view their own run_objects." on run_objects for
    select using (auth.uid() = user_id);
create policy "Individuals can create run_objects." on run_objects for
    insert with check (auth.uid() = user_id);
create policy "Individuals can update their own run_objects." on run_objects for
    update using (auth.uid() = user_id);
create policy "Individuals can delete their own run_objects." on run_objects for
    delete using (auth.uid() = user_id);

-- Policies for run_step_objects
create policy "Individuals can view their own run_step_objects." on run_step_objects for
    select using (auth.uid() = user_id);
create policy "Individuals can create run_step_objects." on run_step_objects for
    insert with check (auth.uid() = user_id);
create policy "Individuals can update their own run_step_objects." on run_step_objects for
    update using (auth.uid() = user_id);
create policy "Individuals can delete their own run_step_objects." on run_step_objects for
    delete using (auth.uid() = user_id);

-- Indexes for foreign keys for message_objects
CREATE INDEX message_objects_user_id ON message_objects (user_id);
CREATE INDEX message_objects_thread_id ON message_objects (thread_id);
CREATE INDEX message_objects_created_at ON thread_objects (created_at);

-- Indexes for common filtering and sorting for thread_objects
CREATE INDEX thread_objects_id ON thread_objects (id);
CREATE INDEX thread_objects_user_id ON thread_objects (user_id);
CREATE INDEX thread_objects_created_at ON thread_objects (created_at);

-- Indexes for common filtering and sorting for run_step_objects
CREATE INDEX run_step_id ON run_step_objects (id);
CREATE INDEX run_step_user_id ON run_step_objects (user_id);
CREATE INDEX run_step_created_at ON run_step_objects (created_at);

-- Indexes for common filtering and sorting for run_objects
CREATE INDEX run_objects_id ON run_objects (id);
CREATE INDEX run_objects_user_id ON run_objects (user_id);
CREATE INDEX run_objects_created_at ON run_objects (created_at);