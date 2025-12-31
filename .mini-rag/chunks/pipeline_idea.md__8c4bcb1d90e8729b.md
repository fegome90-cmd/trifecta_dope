# Pseudocódigo funcional

initial_request: Request = ...

result: Result[FinalCode, Error] = (
    parse_request(initial_request)
    .and_then(load_constitution)
    .and_then(compile_linter_config_in_memory)
    .and_then(run_generative_loop)
    .and_then(run_user_test)
)
