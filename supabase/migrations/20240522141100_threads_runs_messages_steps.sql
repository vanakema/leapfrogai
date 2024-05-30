-- Create a table to store the OpenAI Thread Objects
create table
  thread_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    object text check (object in ('thread')),
    created_at timestamp without time zone DEFAULT NOW(),
    tool_resources jsonb,
    metadata jsonb,
  );

-- Create a table to store the OpenAI Message Objects
create table
  message_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    object text check (object in ('thread.message')),
    created_at timestamp without time zone DEFAULT NOW(),
    thread_id uuid references thread_objects(id),
    status text,
    completed_at timestamp without time zone,
    incomplete_at timestamp without time zone,
    role text,
    content jsonb,
    assistant_id uuid references assistant_objects(id),
    run_id uuid references run_objects(run_id),
    attachments jsonb,
    metadata jsonb
  );

-- Create a table to store the OpenAI Run Objects
create table
  run_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    object text check (object in ('thread.run')),
    created_at timestamp without time zone DEFAULT NOW(),
    thread_id uuid references thread_objects(id),
    assistant_id uuid references assistant_objects(id),
    status text check (status in ('queued', 'in_progress', 'requires_action', 'cancelling', 'cancelled', 'failed', 'completed', 'incomplete', 'expired')),
    required_action jsonb,
    last_error jsonb,
    expires_at timestamp without time zone,
    started_at timestamp without time zone,
    cancelled_at timestamp without time zone,
    failed_at timestamp without time zone,
    completed_at timestamp without time zone,
    incomplete_details jsonb,
    model text,
    instructions text,
    tools jsonb,
    metadata jsonb,
    stream boolean,
    file_ids uuid[],
    incomplete_details jsonb,
    token_usage jsonb,
    temperature float,
    top_p int,
    max_prompts_tokens int,
    max_completion_tokens int,
    truncation_strategy jsonb,
    tool_choice jsonb
    response_format jsonb,
  );

-- Create a table to store the OpenAI Run Step Objects
create table
  run_step_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    object text check (object in ('thread.run.step')),
    created_at timestamp without time zone DEFAULT NOW(),
    assistant_id uuid references assistant_objects(id),
    thread_id uuid references thread_objects(id),
    run_id uuid references run_objects(run_id),
    step_type text,
    status text,
    step_details jsonb,
    last_error jsonb,
    expired_at timestamp without time zone,
    cancelled_at timestamp without time zone,
    failed_at timestamp without time zone,
    completed_at timestamp without time zone,
    metadata jsonb,
    token_usage jsonb
  );

 -- Indexes for common filtering and sorting for run_objects
CREATE INDEX run_objects_created_at ON run_objects (created_at);
CREATE INDEX run_objects_status ON run_objects (status);
CREATE INDEX run_objects_expires_at ON run_objects (expires_at);

 -- Indexes for common filtering and sorting for run_step
CREATE INDEX run_step_objects_status ON run_step_objects (status);

-- Composite indexes for run_objects
CREATE INDEX run_objects_user_id_created_at ON run_objects (user_id, created_at);
CREATE INDEX run_objects_thread_id_created_at ON run_objects (thread_id, created_at);
CREATE INDEX run_objects_status_created_at ON run_objects (status, created_at);
CREATE INDEX run_objects_assistant_id_thread_id ON run_objects (assistant_id, thread_id);

-- Composite indexes for message_objects
CREATE INDEX message_objects_thread_id_created_at ON message_objects (thread_id, created_at);
CREATE INDEX message_objects_user_id_created_at ON message_objects (user_id, created_at);
CREATE INDEX message_objects_created_run_id ON message_objects (created_run_id);

-- Composite indexes for run_step
CREATE INDEX run_step_objects_run_id_created_at ON run_step_objects (run_id, created_at);

-- Indexes for foreign keys for run_objects
CREATE INDEX run_objects_user_id ON run_objects (user_id);
CREATE INDEX run_objects_assistant_id ON run_objects (assistant_id);
CREATE INDEX run_objects_thread_id ON run_objects (thread_id);

-- Indexes for foreign keys for run_step
CREATE INDEX run_step_run_id ON run_step (run_id);
CREATE INDEX run_step_thread_id ON run_step (thread_id);

-- Indexes for foreign keys for message_objects
CREATE INDEX message_objects_user_id ON message_objects (user_id);
CREATE INDEX message_objects_thread_id ON message_objects (thread_id);
CREATE INDEX message_objects_created_run_id ON message_objects (run_id);

-- Indexes for foreign keys for thread_objects
CREATE INDEX thread_objects_user_id ON thread_objects (user_id);