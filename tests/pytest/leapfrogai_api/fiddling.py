from openai.types.beta.threads.run_create_params import RunCreateParamsBase

def test_do_a_thing():
    request: dict = { "assistant_id": "stuff"}
    request_params: RunCreateParamsBase = RunCreateParamsBase(**request)

    print(request_params)