# Mobile Verification Toolkit (MVT)
# Copyright (c) 2021 The MVT Project Authors.
# Use of this software is governed by the MVT License 1.1 that can be found at
#   https://license.mvt.re/1.1/

import io
import csv

from mvt.common.module import DatabaseNotFoundError

from mvt.ios.modules.base import IOSExtraction


class TimeLine(IOSExtraction):
    """This module extracts information about the device and the backup."""

    def __init__(self, file_path=None, base_folder=None, output_folder=None,
                 fast_mode=False, log=None, results=[]):
        super().__init__(file_path=file_path, base_folder=base_folder,
                         output_folder=output_folder, fast_mode=fast_mode,
                         log=log, results=results)

        self.results = {}

def save_timeline(timeline, timeline_path):
    """Save the timeline in a csv file.

    :param timeline: List of records to order and store
    :param timeline_path: Path to the csv file to store the timeline to

    """
    # array=[]
    # data = {}
    # with io.open(timeline_path, "a+", encoding="utf-8") as handle:
    #     # if isinstance(timeline , list):
    #     #     for r in timeline:
    #     #         for k in r:
    #     #             if isinstance( k , datetime ):
    #     #                 k = str(k)
    #     #             elif isinstance( k , dict ):
    #     #                 k = str(k)
    #     #         print(json.dumps(r))
    #     csvoutput = csv.writer(handle, delimiter=",", quotechar="\"")
    #     csvoutput.writerow(["UTC Timestamp", "Plugin", "Event", "Description"])
    #     for event in sorted(timeline, key=lambda x: x["timestamp"] if x["timestamp"] is not None else ""):
    #         csvoutput.writerow([
    #             event.get("timestamp"),
    #             event.get("module"),
    #             event.get("event"),
    #             event.get("data"),
    #         ])
    #     csvReader = csv.DictReader(handle)
    #     for rows in csvReader:
    #         data = rows
    #     timeline.append({"File Name":"Timeline"})


    #         for key in list(data.keys()):  # Use a list instead of a view
    #             if data[key] == '':
    #                 del data[key] 
    #             array.append(data)
    # array=[]
    # data = {'File Name': 'SMS'}
    # array.append(data)
    # os.remove(timeline_path)
