# Mobile Verification Toolkit (MVT)
# Copyright (c) 2021 The MVT Project Authors.
# Use of this software is governed by the MVT License 1.1 that can be found at
#   https://license.mvt.re/1.1/

import plistlib

from mvt.common.utils import convert_timestamp_to_iso

from ..base import IOSExtraction

OSANALYTICS_ADDAILY_BACKUP_IDS = [
    "f65b5fafc69bbd3c60be019c6e938e146825fa83",
]
OSANALYTICS_ADDAILY_ROOT_PATHS = [
    "private/var/mobile/Library/Preferences/com.apple.osanalytics.addaily.plist",
]


class OSAnalyticsADDaily(IOSExtraction):
    """Extract network usage information by process, from com.apple.osanalytics.addaily.plist"""

    def __init__(self, file_path=None, base_folder=None, output_folder=None,
                 fast_mode=False, log=None, results=[]):
        super().__init__(file_path=file_path, base_folder=base_folder,
                         output_folder=output_folder, fast_mode=fast_mode,
                         log=log, results=results)

    def serialize(self, record):
        record_data = f"{record['package']} WIFI IN: {record['wifi_in']}, WIFI OUT: {record['wifi_out']} - "  \
                      f"WWAN IN: {record['wwan_in']}, WWAN OUT: {record['wwan_out']}"
        return {
            "timestamp": record["ts"],
            "module": self.__class__.__name__,
            "event": "osanalytics_addaily",
            "data": record_data,
        }

    def check_indicators(self):
        if not self.indicators:
            return

        for result in self.results:
            if self.indicators.check_process(result["package"]):
                self.detected.append(result)

    def run(self):
        self._find_ios_database(backup_ids=OSANALYTICS_ADDAILY_BACKUP_IDS,
                                root_paths=OSANALYTICS_ADDAILY_ROOT_PATHS)
        self.log.info("Found com.apple.osanalytics.addaily plist at path: %s", self.file_path)

        with open(self.file_path, "rb") as handle:
            file_plist = plistlib.load(handle)

        for app, values in file_plist.get("netUsageBaseline", {}).items():
            self.results.append({
                "@timestamp": convert_timestamp_to_iso(values[0]),
                "package": app,
                "ts": convert_timestamp_to_iso(values[0]),
                "wifi_in": values[1],
                "wifi_out": values[2],
                "wwan_in": values[3],
                "wwan_out": values[4],
            })

        self.log.info("Extracted a total of %d com.apple.osanalytics.addaily entries", len(self.results))
