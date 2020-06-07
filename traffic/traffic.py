import math
import sys
import time

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


def get_current_bytes(network_interface):
    data = psutil.net_io_counters(pernic=True)[network_interface]
    return data.bytes_recv, data.bytes_sent


def format_bytes(speed):
    if speed == 0:  # log(0) will error out
        return "0B"
    sl = math.log(speed)
    factor = int(math.floor(sl / math.log(1024)))
    speed_unit = ["B", "KB", "MB", "GB", "TB", "PB"][factor]
    if factor > 1:
        return str(round(speed / 1024 ** factor, 1)) + speed_unit
    else:
        return str(int(speed / 1024 ** factor)) + speed_unit


def print_speed(
    network_interface,
    down_speed,
    up_speed,
    down_bytes_total,
    up_bytes_total,
    offline=False,
    final=False,
):
    CURSOR_UP_ONE = "\x1b[1A"
    ERASE_LINE = "\x1b[2K"
    HIDE_CURSOR = "\x1b[?25l"
    SHOW_CURSOR = "\x1b[?25h"
    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.write(ERASE_LINE)
    sys.stdout.write(
        "\rInterface: %s %s" % (network_interface, "[offline]" if offline else "")
    )
    sys.stdout.write(
        "\r\nDown: %s%s .. %s/s%s\n\r  Up: %s%s .. %s/s%s"
        % (
            bcolors.GREEN,
            format_bytes(down_bytes_total),
            ("avg:" if final else "") + format_bytes(down_speed),
            bcolors.ENDC,
            bcolors.BLUE,
            format_bytes(up_bytes_total),
            ("avg:" if final else "") + format_bytes(up_speed),
            bcolors.ENDC,
        )
    )

    if not final:
        sys.stdout.write(ERASE_LINE)
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)
        sys.stdout.write(CURSOR_UP_ONE)
    else:
        sys.stdout.write("\n")
        sys.stdout.write(SHOW_CURSOR)


def print_help():
    print(
        """traffic - a tool to view your network speed
Usage: traffic [options] [device]

- see the network stats on your main device
    $ traffic
- specify a network device
    $ traffic en0
- list all network devices
    $ traffic -l
- view this help
    $ traffic -h

https://github.com/meain/traffic"""
    )


def print_network_devices(counters_bytes_rec):
    for nib in counters_bytes_rec:
        if nib[1] > 0:
            sys.stdout.write(
                "%s%s: %s%s\n"
                % (bcolors.GREEN, nib[0], format_bytes(nib[1]), bcolors.ENDC)
            )
        else:
            sys.stdout.write("%s: %s\n" % (nib[0], format_bytes(nib[1])))


def main():
    # setup
    counters = psutil.net_io_counters(pernic=True)
    counters_bytes_rec = [(c, counters[c][1]) for c in counters.keys()]
    counters_bytes_rec = sorted(counters_bytes_rec, key=lambda x: x[1], reverse=True)
    network_interface = list(counters_bytes_rec[0])[0]

    if len(sys.argv) > 1:
        if sys.argv[1] == "-h" or sys.argv[1] == "--help":
            print_help()
            return

        if sys.argv[1] == "-l":
            print_network_devices(counters_bytes_rec)
            return

        if sys.argv[1] in [s[0] for s in counters_bytes_rec]:
            network_interface = sys.argv[1]
        else:
            print(f"{bcolors.RED}Unknown network device `{sys.argv[1]}`{bcolors.ENDC}")
            print("Use `traffic -l` to view list of devices")
            exit(1)

    # initialize
    start_time = time.time()
    start_down_bytes, start_up_bytes = get_current_bytes(
        network_interface
    )  # unlikely we get a exception here
    last_down_bytes, last_up_bytes = start_down_bytes, start_up_bytes
    last_time = start_time
    down_speed = 0
    up_speed = 0
    down_bytes_total = 0
    up_bytes_total = 0
    offline = False

    try:
        # main loop
        while True:
            print_speed(
                network_interface,
                down_speed,
                up_speed,
                down_bytes_total,
                up_bytes_total,
                offline,
            )
            time.sleep(1)

            try:
                down_bytes, up_bytes = get_current_bytes(network_interface)
                offline = False
            except KeyError:
                offline = True
            now = time.time()

            # current speed
            down_speed = (last_down_bytes - down_bytes) / (last_time - now)
            up_speed = (last_up_bytes - up_bytes) / (last_time - now)

            # total transfer
            down_bytes_total = down_bytes - start_down_bytes
            up_bytes_total = up_bytes - start_up_bytes

            last_down_bytes, last_up_bytes = down_bytes, up_bytes
            last_time = now
    except KeyboardInterrupt:
        now = time.time()

        # avg and total
        down_speed_avg = (down_bytes - start_down_bytes) / (now - start_time)
        up_speed_avg = (up_bytes - start_up_bytes) / (now - start_time)
        down_bytes_total = down_bytes - start_down_bytes
        up_bytes_total = up_bytes - start_up_bytes
        print_speed(
            network_interface,
            down_speed_avg,
            up_speed_avg,
            down_bytes_total,
            up_bytes_total,
            offline,
            True,
        )


if __name__ == "__main__":
    main()
