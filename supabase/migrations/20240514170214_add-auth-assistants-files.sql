alter table assistant_objects
    add column user_id uuid references auth.users not null;

alter table file_objects
        add column user_id uuid references auth.users not null;
