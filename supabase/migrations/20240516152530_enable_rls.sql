-- RLS policies
alter table assistant_objects enable row level security;
alter table file_objects enable row level security;
alter table vector_store_objects enable row level security;

-- Policies for assistant_objects
create policy "Individuals can view their own assistant_objects. " on assistant_objects for
    select using (auth.uid() = user_id);
create policy "Individuals can create assistant_objects." on assistant_objects for
    insert with check (auth.uid() = user_id);
create policy "Individuals can update their own assistant_objects." on assistant_objects for
    update using (auth.uid() = user_id);
create policy "Individuals can delete their own assistant_objects." on assistant_objects for
    delete using (auth.uid() = user_id);

-- Policies for file_objects
create policy "Individuals can view their own file_objects." on file_objects for
    select using (auth.uid() = user_id);
create policy "Individuals can create file_objects." on file_objects for
    insert with check (auth.uid() = user_id);
create policy "Individuals can update their own file_objects." on file_objects for
    update using (auth.uid() = user_id);
create policy "Individuals can delete their own file_objects." on file_objects for
    delete using (auth.uid() = user_id);

-- Policies for file_bucket
create policy "Authenticated individuals can add files to file_bucket."
on storage.objects for
    insert to authenticated with check (bucket_id = 'file_bucket');
create policy "Authenticated individuals can view files in the file_bucket."
on storage.objects for
    select to authenticated using (bucket_id = 'file_bucket');
create policy "Authenticated individuals can delete files in the file_bucket."
on storage.objects for
    delete to authenticated using (bucket_id = 'file_bucket');

-- Policies for vector_store_objects
create policy "Individuals can view their own vector_store_objects." on vector_store_objects for
    select using (auth.uid() = user_id);
create policy "Individuals can create vector_store_objects." on vector_store_objects for
    insert with check (auth.uid() = user_id);
create policy "Individuals can update their own vector_store_objects." on vector_store_objects for
    update using (auth.uid() = user_id);
create policy "Individuals can delete their own vector_store_objects." on vector_store_objects for
    delete using (auth.uid() = user_id);
