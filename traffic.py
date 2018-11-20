import sys
import time
import math
import psutil


class bcolors:
    PINK = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


counters = psutil.net_io_counters(pernic=True)
if "en0" not in counters:
    print("Could not find a network interface")
    exit(1)


def get_current_bytes():
    data = psutil.net_io_counters(pernic=True)["en0"]
    down_bytes = data.bytes_recv
    up_bytes = data.bytes_sent
    return down_bytes, up_bytes


def format_speed(speed):
    if speed == 0:
        return "0 B"
    factor = int(math.floor(math.log(speed) / math.log(1024)))
    return (
        str(int(speed / 1024 ** factor))
        + " "
        + ["B", "KB", "MB", "GB", "TB", "PB"][factor]
    )


def print_speed(down_speed, up_speed, final=False):
    CURSOR_UP_ONE = "\x1b[1A"
    ERASE_LINE = "\x1b[2K"
    sys.stdout.write(
        "\rDown: %s%s%s\n\r  Up: %s%s%s\n"
        % (
            bcolors.GREEN,
            format_speed(down_speed),
            bcolors.ENDC,
            bcolors.BLUE,
            format_speed(up_speed),
            bcolors.ENDC,
        )
    )
    if not final:
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)


start_time = int(time.time())


data = None

start_time = time.time()
start_down_bytes, start_up_bytes = get_current_bytes()
last_down_bytes, last_up_bytes = start_down_bytes, start_up_bytes
last_time = start_time

down_speed = 0
up_speed = 0

try:
    while True:
        print_speed(down_speed, up_speed)
        time.sleep(1)

        down_bytes, up_bytes = get_current_bytes()
        now = time.time()

        down_speed = (last_down_bytes - down_bytes) / (last_time - now)
        up_speed = (last_up_bytes - up_bytes) / (last_time - now)

        last_down_bytes, last_up_bytes = down_bytes, up_bytes
        last_time = now
except KeyboardInterrupt:
    print("\rAverage speed")
    down_bytes, up_bytes = get_current_bytes()
    now = time.time()
    down_speed = (start_down_bytes - down_bytes) / (start_time - now)
    up_speed = (start_up_bytes - up_bytes) / (start_time - now)
    print_speed(down_speed, up_speed, True)
