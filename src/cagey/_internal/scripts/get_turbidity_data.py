# ruff: noqa: T201

import argparse
import time
from pathlib import Path
import cagey


def main() -> None:
    args = _parse_args()
    monitor = cagey.turbidity.Monitor(
        args.output_directory,
        tm_n_minutes=1,
        tm_range_limit=3,
        tm_std_max=2,  # std_max: maximum standard deviation the data can have to be determined as stable
        tm_sem_max=2,  # sem_max: maximum standard error the data can have to be determined as stable
        tm_upper_limit=1,
    )
    monitor.start_monitoring()
    start_time = time.time()
    while (time_since_start := _time_since(start_time)) < args.time_out:
        print("hi")
        monitor.get_turbidity_data()
        if monitor.state != "unstable_state":
            monitor.stop_monitoring()
            print(f"Finished: {monitor.state}")
            return
        time_left = max(0, args.time_out - time_since_start)
        time.sleep(min(time_left, args.sample_rate))

    monitor.stop_monitoring()
    print(f"Finished: {args.time} seconds reached - {monitor.state}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--time-out", type=int, default=200)
    parser.add_argument("--sample-rate", type=int, default=10)
    return parser.parse_args()


def _time_since(start_time: float) -> float:
    return time.time() - start_time
