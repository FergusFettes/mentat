import concurrent.futures
import os
import subprocess
import sys
import threading
from textwrap import dedent

import pytest
from git import Repo

from mentat.app import run
from mentat.user_input_manager import UserInputManager, UserQuitInterrupt

threadLocal = threading.local()


def exercise_passed():
    try:
        with open(threadLocal.test_output_file, "r") as f:
            lines = f.readlines()
            return "failed" not in lines[-1] and "passed" in lines[-1]
    except FileNotFoundError:
        return False


def get_error_message():
    with open(threadLocal.test_output_file, "r") as f:
        lines = f.readlines()
        lines = lines[-30:]
        return "\n".join(lines)


def run_exercise_test():
    try:
        proc = subprocess.run(
            ["pytest", threadLocal.exercise], stdout=subprocess.PIPE, timeout=1
        )
        results = proc.stdout.decode("utf-8")
    except subprocess.TimeoutExpired:
        results = "Test timed out"
    with open(threadLocal.test_output_file, "w") as f:
        f.write(results)


@pytest.fixture
def mock_user_input_manager(max_iterations, mocker):
    def mocked_collect_user_input(self, use_plain_session=False):
        if threadLocal.iterations == 0:
            threadLocal.iterations = 1
            threadLocal.confirm = True
            return "Please complete the stub program you have been given."
        else:
            if threadLocal.confirm:
                threadLocal.confirm = False
                return "y"
            run_exercise_test()
            if threadLocal.iterations >= max_iterations or exercise_passed():
                raise UserQuitInterrupt()
            else:
                threadLocal.iterations += 1
                threadLocal.confirm = True
                return "Please fix this error:\n" + get_error_message()

    mocker.patch.object(
        UserInputManager, "collect_user_input", new=mocked_collect_user_input
    )


@pytest.fixture
def clone_exercism_python_repo(start_at):
    exercism_url = "https://github.com/exercism/python.git"

    local_dir = f"{os.path.dirname(__file__)}/../../../exercism-python"
    if start_at != 0:
        if os.path.exists(local_dir):
            repo = Repo(local_dir)
            repo.git.reset("--hard")
            repo.remotes.origin.pull()
        else:
            repo = Repo.clone_from(exercism_url, local_dir)
    os.chdir(local_dir)


@pytest.fixture
def num_exercises(request):
    return int(request.config.getoption("--num_exercises"))


@pytest.fixture
def max_iterations(request):
    return int(request.config.getoption("--max_iterations"))


@pytest.fixture
def start_at(request):
    return int(request.config.getoption("--start_at"))


@pytest.fixture
def max_workers(request):
    return int(request.config.getoption("--max_workers"))


def run_exercise(problem_dir):
    sys.__stdout__.write(f"\nStarting {problem_dir}")
    threadLocal.exercise = f"exercises/practice/{problem_dir}"
    threadLocal.test_output_file = f"{threadLocal.exercise}/test_output.txt"
    threadLocal.iterations = 0
    problem_file = problem_dir.replace("-", "_")
    run(
        [f"{threadLocal.exercise}/{problem_file}.py"],
        no_code_map=True,
    )
    passed = exercise_passed()
    sys.__stdout__.write(
        f"\nFinished {problem_dir} in {threadLocal.iterations} iterations {passed}"
    )
    return {
        "iterations": threadLocal.iterations,
        "passed": passed,
        "test": problem_dir,
    }


def test_practice_directory_performance(
    mock_user_input_manager,
    clone_exercism_python_repo,
    num_exercises,
    max_iterations,
    max_workers,
    start_at,
):
    exercises = os.listdir("exercises/practice")[start_at:num_exercises]
    num_exercises = len(exercises)
    sys.stdout = open("mentat_output.txt", "w")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(run_exercise, exercises))
        first_iteration = len(
            [
                result
                for result in results
                if result["iterations"] == 1 and result["passed"]
            ]
        )
        eventually = len([result for result in results if result["passed"]])
        sys.stdout.close()
        sys.stdout = sys.__stdout__
        print(dedent(f"""
            Results: {results}
            Passed in first attempt: {first_iteration}/{num_exercises}
            Passed in {max_iterations} attempts: {eventually}/{num_exercises}"""))
