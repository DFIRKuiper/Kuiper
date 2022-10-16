# Mobile Verification Toolkit (MVT)
# Copyright (c) 2021 The MVT Project Authors.
# Use of this software is governed by the MVT License 1.1 that can be found at
#   https://license.mvt.re/1.1/

import os
import plistlib

from mvt.common.module import DatabaseNotFoundError

from mvt.ios.modules.base import IOSExtraction


class InstalledApplications(IOSExtraction):
    """This module extracts information about the device and the backup."""

    def __init__(self, file_path=None, base_folder=None, output_folder=None,
                 fast_mode=False, log=None, results=[]):
        super().__init__(file_path=file_path, base_folder=base_folder,
                         output_folder=output_folder, fast_mode=fast_mode,
                         log=log, results=results)

        self.results = []

    def run(self):
        info_path = os.path.join(self.base_folder, "Info.plist")
        if not os.path.exists(info_path):
            raise DatabaseNotFoundError("No Info.plist at backup path, unable to extract device information")

        with open(info_path, "rb") as handle:
            info = plistlib.load(handle)
            apps = info.get("Installed Applications", None)
            self.log.info("%s: %s", "Installed Applications", apps)
            for app in apps:
                self.results.append({"installed_app" : app})

