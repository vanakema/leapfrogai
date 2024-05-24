-- Create a table to store the OpenAI Thread Objects
create table
  thread_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    created_at timestamp without time zone DEFAULT NOW(),
    metadata jsonb,
  );

-- Create a table to store the OpenAI Message Objects
create table
  message_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    created_at timestamp without time zone DEFAULT NOW(),
    thread_id uuid references thread_objects(id),
    role text,
    created_run_id references run_objects(run_id), -- The run_id the message was created by
    content jsonb,
    metadata jsonb
  );

-- Create a table to store the OpenAI Message File Objects
create table
  message_file_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    created_at timestamp without time zone DEFAULT NOW(),
    message_id uuid references message_objects(id),
    file_id uuid references file_objects(id)
  );

CREATE TYPE run_status AS ENUM ('queued', 'in_progress', 'requires_action', 'cancelling', 'cancelled', 'failed', 'completed', 'incomplete', 'expired');

-- Create a table to store the OpenAI Run Objects
create table
  run_objects (
    run_id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    created_at timestamp without time zone DEFAULT NOW(),
    assistant_id uuid references assistant_objects(id),
    thread_id uuid references thread_objects(id),
    status run_status,
    started_at timestamp without time zone,
    expires_at timestamp without time zone,
    cancelled_at timestamp without time zone,
    failed_at timestamp without time zone,
    completed_at timestamp without time zone,
    last_error jsonb,
    model text,
    instructions text,
    stream boolean,
    tools text[],
    file_ids uuid[],
    metadata jsonb,
    incomplete_details jsonb,
    token_usage jsonb,
    temperature float,
    max_prompts_tokens int,
    max_completion_tokens int,
    truncation_strategy jsonb,
    response_format jsonb,
    tool_choice jsonb
  );

-- Create a table to store the OpenAI Run Step Objects
create table
  run_step_objects (
    step_id uuid primary key DEFAULT uuid_generate_v4(),
    created_at timestamp without time zone DEFAULT NOW(),
    run_id uuid references run_objects(run_id),
    thread_id uuid references thread_objects(id),
    step_type text,
    status text,
    cancelled_at timestamp without time zone,
    completed_at timestamp without time zone,
    expired_at timestamp without time zone,
    failed_at timestamp without time zone,
    last_error jsonb,
    step_details jsonb,
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
CREATE INDEX message_objects_created_run_id ON message_objects (created_run_id);

-- Indexes for foreign keys for thread_objects
CREATE INDEX thread_objects_user_id ON thread_objects (user_id);