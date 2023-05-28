import inspect
import textwrap


def convert_function_to_text(func):
    source, _ = inspect.getsourcelines(func)
    return textwrap.dedent(''.join(source))


def misc_schedular():
    pass
    # query db every 30 sec
    # check for timestamp col and see if any task needs to run
    # if current timestamp >= record timestamp, send task to run_in_thread function
    # run_in_thread function will take function as arg, next_run_time in timestamp,
    # run it, wait for the task to complete then call join. update schedular table
    # schedular table will have columns, function_name, serialized_function, readable_function last_run, next_run,
    # interval_in_minutes, is_enabled, run_counts
