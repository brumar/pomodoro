#! /usr/bin/python3
import argparse
from subprocess import call
from threading import Thread

from constants import *
from util import timedelta_str, Stage, PomodoroState

MAX_LINE_LEN = 50
ONE_TIME_ONLY = True
_kill = False

pomo_state = None

# TODO: use dunst
def notify_user(title, message):
    if ENABLE_DESKTOP_NOTIFS:
        try:
            call(['notify-send', title, message, '-t', '1000'])
        except FileNotFoundError:
            print("Skipping desktop notification because `notify-send` wasn't recognized.")


def update_progress_line(td):
    print(timedelta_str(td).ljust(MAX_LINE_LEN), end='\r')


def run_stage(stage, progress_callback=None):
    global pomo_state
    t = Thread(target=pomo_state.run, args=(stage, 0.2, progress_callback))
    t.start()
    try:
        t.join()
    except KeyboardInterrupt as interrupt:
        pomo_state.kill()
        t.join()
        raise interrupt

parser = argparse.ArgumentParser(description='A Pomodoro CLI.')
parser.add_argument('--interactive', dest='interactive', action='store_true')
parser.add_argument('--cycle', dest='cycle', action='store_false')
parser.add_argument('--minutes', dest='minutes', type=int, default=ACTIVE_STAGE_MINUTES)
parser.add_argument('--goal', dest='goal', type=str, default="")
args = parser.parse_args()

if args.goal:
    with open("/home/bruno/pomodoro/history.txt", "w") as hist_file:
        hist_file.write(f"{args.minutes} : {args.goal}")

if args.interactive:
    print("Running in interactive mode")
    try:
        pomo_state = PomodoroState(ACTIVE_STAGE_MINUTES, REST_STAGE_MINUTES, STATE_FILE)
        while True:
            input("Press <enter> to begin a pomodoro.")
            run_stage(Stage.ACTIVE, progress_callback=update_progress_line)
            pomo_state.prep_for_rest()

            notify_user("Pomodoro #%d completed" % pomo_state.pomos_completed, "Time for the rest stage")
            print("Time for the rest stage.")
            run_stage(Stage.REST, progress_callback=update_progress_line)
            pomo_state.prep_for_active()

            notify_user("Rest stage #%d completed" % pomo_state.pomos_completed,
                        "Go to the CLI to start pomodoro #%d" % (pomo_state.pomos_completed + 1))
            print("Rest stage finished - You've completed %d pomodoro(s)." % pomo_state.pomos_completed)
    except KeyboardInterrupt:
        pomo_state.kill()
    print("Finished - You completed a total of %d pomodoro(s)." % pomo_state.pomos_completed)
else:
    # Non-interactive, should be able to just run in the background.
    print("Running in non-interactive mode")
    pomo_state = PomodoroState(args.minutes, REST_STAGE_MINUTES, STATE_FILE)
    while True:
        run_stage(Stage.ACTIVE)
        notify_user("Pomodoro completed", "Time for the rest stage")
        break
        if not args.cycle:
            break
        pomo_state.prep_for_rest()
        run_stage(Stage.REST)
        pomo_state.prep_for_active()
        notify_user("Rest stage completed", "Time to get back to work")
