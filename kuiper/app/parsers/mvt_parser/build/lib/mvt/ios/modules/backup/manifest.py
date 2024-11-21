# Mobile Verification Toolkit (MVT)
# Copyright (c) 2021 The MVT Project Authors.
# Use of this software is governed by the MVT License 1.1 that can be found at
#   https://license.mvt.re/1.1/

import datetime
import io
import os
import plistlib
import sqlite3

from mvt.common.module import DatabaseNotFoundError
from mvt.common.utils import convert_timestamp_to_iso

from mvt.ios.modules.base import IOSExtraction


class Manifest(IOSExtraction):
    """This module extracts information from a backup Manifest.db file."""

    def __init__(self, file_path=None, base_folder=None, output_folder=None,
                 fast_mode=False, log=None, results=[]):
        super().__init__(file_path=file_path, base_folder=base_folder,
                         output_folder=output_folder, fast_mode=fast_mode,
                         log=log, results=results)

    def _get_key(self, dictionary, key):
        """Unserialized plist objects can have keys which are str or byte types
        This is a helper to try fetch a key as both a byte or string type.

        :param dictionary:
        :param key:

        """
        return dictionary.get(key.encode("utf-8"), None) or dictionary.get(key, None)

    @staticmethod
    def _convert_timestamp(timestamp_or_unix_time_int):
        """Older iOS versions stored the manifest times as unix timestamps.

        :param timestamp_or_unix_time_int:

        """
        if isinstance(timestamp_or_unix_time_int, datetime.datetime):
            return convert_timestamp_to_iso(timestamp_or_unix_time_int)
        else:
            timestamp = datetime.datetime.utcfromtimestamp(timestamp_or_unix_time_int)
            return convert_timestamp_to_iso(timestamp)

    def serialize(self, record):
        records = []
        if "modified" not in record or "status_changed" not in record:
            return
        for ts in set([record["created"], record["modified"], record["status_changed"]]):
            macb = ""
            macb += "M" if ts == record["modified"] else "-"
            macb += "-"
            macb += "C" if ts == record["status_changed"] else "-"
            macb += "B" if ts == record["created"] else "-"

            records.append({
                "timestamp": ts,
                "module": self.__class__.__name__,
                "event": macb,
                "data": f"{record['relative_path']} - {record['domain']}"
            })

        return records

    def check_indicators(self):
        if not self.indicators:
            return

        for result in self.results:
            if "relative_path" not in result:
                continue
            if not result["relative_path"]:
                continue

            if result["domain"]:
                if os.path.basename(result["relative_path"]) == "com.apple.CrashReporter.plist" and result["domain"] == "RootDomain":
                    self.log.warning("Found a potentially suspicious \"com.apple.CrashReporter.plist\" file created in RootDomain")
                    self.detected.append(result)
                    continue

            if self.indicators.check_file_name(result["relative_path"]):
                self.log.warning("Found a known malicious file at path: %s", result["relative_path"])
                self.detected.append(result)
                continue

            relPath = result["relative_path"].lower()
            for ioc in self.indicators.ioc_domains:
                if ioc.lower() in relPath:
                    self.log.warning("Found mention of domain \"%s\" in a backup file with path: %s",
                                     ioc, relPath)
                    self.detected.append(result)

    def run(self):
        manifest_db_path = os.path.join(self.base_folder, "Manifest.db")
        if not os.path.isfile(manifest_db_path):
            raise DatabaseNotFoundError("unable to find backup's Manifest.db")

        self.log.info("Found Manifest.db database at path: %s", manifest_db_path)

        conn = sqlite3.connect(manifest_db_path)
        cur = conn.cursor()

        cur.execute("SELECT * FROM Files;")
        names = [description[0] for description in cur.description]

        for file_entry in cur:
            file_data = {}
            for index, value in enumerate(file_entry):
                file_data[names[index]] = value

            cleaned_metadata = {
                "file_id": file_data["fileID"],
                "domain": file_data["domain"],
                "relative_path": file_data["relativePath"],
                "flags": file_data["flags"],
                "created": "",
            }

            if file_data["file"]:
                try:
                    file_plist = plistlib.load(io.BytesIO(file_data["file"]))
                    file_metadata = self._get_key(file_plist, "$objects")[1]
                    cleaned_metadata.update({
                        "@timestamp": self._convert_timestamp(self._get_key(file_metadata, "Birth")),                        
                        "created": self._convert_timestamp(self._get_key(file_metadata, "Birth")),
                        "modified": self._convert_timestamp(self._get_key(file_metadata, "LastModified")),
                        "status_changed": self._convert_timestamp(self._get_key(file_metadata, "LastStatusChange")),
                        "mode": oct(self._get_key(file_metadata, "Mode")),
                        "owner": self._get_key(file_metadata, "UserID"),
                        "size": self._get_key(file_metadata, "Size"),
                    })
                except Exception:
                    self.log.exception("Error reading manifest file metadata for file with ID %s and relative path %s",
                                       file_data["fileID"], file_data["relativePath"])
                    pass

            self.results.append(cleaned_metadata)

        cur.close()
        conn.close()

        self.log.info("Extracted a total of %d file metadata items", len(self.results))
