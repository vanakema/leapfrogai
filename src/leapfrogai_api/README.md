# LeapfrogAI API

A mostly OpenAI compliant API surface.

## Local Development Setup

### Requirements

1. Install dependencies
    ```bash
    make install
    ```

2. Create a local Supabase instance (requires [Supabase CLI](https://supabase.com/docs/guides/cli/getting-started)):
    ```bash
    brew install supabase/tap/supabases

    supabase start # from /leapfrogai

    supabase stop --project-id leapfrogai_api # stop api containers

    supabase db reset # clears all data and reinitializes migrations

    supabase status # to check status and see your keys
    ```

3. Create a local api user
    ```bash
    make supabase-user
    ```

### Session Authentication

4. Create a JWT token
    ```bash
    make supabase-jwt-token
    source .jwt
    ```
    This will export an environment variable `SUPABASE_USER_JWT` and create a file called `.jwt` to save it.


5. Make calls to the api swagger endpoint at `http://localhost:8080/docs` using your JWT token as the `HTTPBearer` token. 
   * Hit `Authorize` on the swagger page to enter your JWT token

## Integration Tests

The integration tests serve to identify any mismatches between components:

- Check all API routes
- Validate Request/Response types
- DB CRUD operations
- Schema mismatches

Integration tests require a Supabase instance and environment variables configured (see [Local Development](#local-development)).

Also requires a JWT environment variable that is only used for tests:

``` bash
export SUPABASE_USER_JWT="<your JWT>"
```


From this directory run:

``` bash
make test-integration
```

## Notes

* All API calls to `assistants` or `files` endpoints must be authenticated via a Supabase JWT token in the message's `Authorization` header.
