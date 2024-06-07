import os
from dotenv import load_dotenv


def pytest_addoption(parser):
    # Add a parameter option to the `pytest` call
    parser.addoption(
        "--env-dir",
        action="store",
        default=None,
        help="Directory containing .env files",
    )


def pytest_configure(config):
    # runs once for all tests

    env_dir = config.getoption("env_dir") or ""
    print(f" >>> Loading .env from {env_dir}")
    load_dotenv(os.path.join(env_dir, ".jwt"))

    os.environ["SUPABASE_USER_JWT"] = os.environ.get("SUPABASE_USER_JWT", "mock-data")

    os.environ["ANON_KEY"] = "mock-data"
    os.environ["API_KEY"] = "mock-data"
