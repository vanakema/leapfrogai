-- Create a table to store the OpenAI Thread Objects
create table
  thread_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    created_at bigint default extract(epoch from now()) not null,
    metadata jsonb,
  );

-- Create a table to store the OpenAI Message Objects
create table
  message_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    created_at bigint default extract(epoch from now()) not null,
    thread_id uuid references thread_objects(id),
    role text,
    content jsonb,
    metadata jsonb
  );

-- Create a table to store the OpenAI Message File Objects
create table
  message_file_objects (
    id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    created_at bigint default extract(epoch from now()) not null,
    message_id uuid references message_objects(id),
    file_id uuid references file_objects(id)
  );

-- Create a table to store the OpenAI Run Objects
create table
  run_objects (
    run_id uuid primary key DEFAULT uuid_generate_v4(),
    user_id uuid references auth.users not null,
    created_at bigint default extract(epoch from now()) not null,
    assistant_id uuid references assistant_objects(id),
    thread_id uuid references thread_objects(id),
    status text,
    started_at bigint,
    expires_at bigint,
    cancelled_at bigint,
    failed_at bigint,
    completed_at bigint,
    last_error jsonb,
    model text,
    instructions text,
    tools text[],
    file_ids uuid[],
    metadata jsonb,
    incomplete_details jsonb,
    usage jsonb,
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
    object text,
    created_at bigint default extract(epoch from now()) not null,
    run_id uuid,
    assistant_id uuid,
    thread_id uuid,
    type text,
    status text,
    cancelled_at bigint,
    completed_at bigint,
    expired_at bigint,
    failed_at bigint,
    last_error jsonb,
    step_details jsonb,
    usage jsonb
  );