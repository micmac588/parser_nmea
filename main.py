#!/usr/bin/env python3
import argparse
import logging
import multiprocessing
import threading
import pynmea2

from scatter_plotter import ScatterPlotter

MIN_SPEED = 5
INVALID_HEADING = 1000

def prepare_logger(logger_name, verbosity, log_file=None):
    """Initialize and set the logger.

    :param logger_name: the name of the logger to create
    :type logger_name: string
    :param verbosity: verbosity level: 0 -> default, 1 -> info, 2 -> debug
    :type  verbosity: int
    :param log_file: if not None, file where to save the logs.
    :type  log_file: string (path)
    :return: a configured logger
    :rtype: logging.Logger
    """

    logging.getLogger('parse').setLevel(logging.ERROR)

    logger = logging.getLogger(logger_name)

    log_level = logging.WARNING - (verbosity * 10)
    log_format = "[%(filename)-30s:%(lineno)-4d][%(levelname)-7s] %(message)s"
    logging.basicConfig(format=log_format, level=log_level)

    # create and add file logger
    if log_file:
        formatter = logging.Formatter(log_format)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

def get_delta_heading(bottom_heading, compass_heading):
    '''
    Calculate the difference beetween bottom_heading and compass_heading
    '''
    
    delta_heading = bottom_heading - compass_heading
    if delta_heading > 180:
        delta_heading = 360 - delta_heading
    if delta_heading < -180:
        delta_heading = 360 + delta_heading
    return delta_heading

def parse_file(inputfile, queue_delta_heading):
    bottom_heading = INVALID_HEADING
    compass_heading = INVALID_HEADING
    previous_delta_heading = INVALID_HEADING
    previous_bottom_heading = INVALID_HEADING
    sog = 0
    fail = 0
    with open(inputfile, "r") as fi:
        queue_delta_heading.put(['Start', inputfile, 'delta heading', 'heading'])
        for line in fi:
            try:
                msg = pynmea2.parse(line[12:])
                try:
                    if msg.sentence_type == 'VTG':
                        bottom_heading = msg.true_track
                        sog = msg.spd_over_grnd_kts
                        # print(repr(msg))
                    if msg.sentence_type =='VHW':
                        compass_heading = msg.heading_true  # msg.heading_magnetic
                except Exception as e:
                    # print(e)
                    continue
            except pynmea2.ParseError as e:
                #print('Parse error: {}'.format(e))
                fail += 1
                continue
            if sog > MIN_SPEED:  # bottom heading is not accurate when sog is too low
                # print(f"bottom {bottom_heading} compass {compass_heading}")
                delta_heading = get_delta_heading(int(bottom_heading), int(compass_heading))
                if (delta_heading != previous_delta_heading) or (bottom_heading != previous_bottom_heading):
                    previous_delta_heading = delta_heading
                    previous_bottom_heading = bottom_heading
                    queue_delta_heading.put([delta_heading, int(bottom_heading)])


        queue_delta_heading.put(['Stop',])


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", help="the nmea log file.", required=True)
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase the verbosity", required=False)
    parser.add_argument("-l", "--logfile", help="log file name", required=False)

    args = parser.parse_args()

    logger = prepare_logger("nmea_parser", args.verbosity, args.logfile)
    queue_delta_heading = multiprocessing.Queue()
    plotter_delta_heading = ScatterPlotter(queue_delta_heading, logger)

    plotter_delta_heading.start()

    logger.info(f"Start parsing of {args.inputfile}")
    parser = threading.Thread(target=parse_file, args=(args.inputfile, queue_delta_heading))
    parser.start()
    parser.join()
    logger.info(f"End of parsing {args.inputfile}")
    plotter_delta_heading.join()
    logger.info(f"End of plotting")


    

if __name__ == "__main__":
    main()
