
# Mobile Verification Toolkit (MVT)
# Copyright (c) 2021 The MVT Project Authors.
# Use of this software is governed by the MVT License 1.1 that can be found at
#   https://license.mvt.re/1.1/

import os
import plistlib
from base64 import b64encode

from mvt.common.utils import convert_timestamp_to_iso

from mvt.ios.modules.base import IOSExtraction

CONF_PROFILES_DOMAIN = "SysSharedContainerDomain-systemgroup.com.apple.configurationprofiles"


class ConfigurationProfiles(IOSExtraction):
    """This module extracts the full plist data from configuration profiles."""

    def __init__(self, file_path=None, base_folder=None, output_folder=None,
                 fast_mode=False, log=None, results=[]):
        super().__init__(file_path=file_path, base_folder=base_folder,
                         output_folder=output_folder, fast_mode=fast_mode,
                         log=log, results=results)

    def serialize(self, record):
        if not record["install_date"]:
            return

        print("saleh: " + str(record['plist']))
        payload_name = record['plist']
        payload_description = record['plist']
        self.log.info("saleh: " + payload_name)
        return {
            "timestamp": record["install_date"],
            "module": self.__class__.__name__,
            "event": "configuration_profile_install",
            "data": f"{record['plist']['PayloadType']} installed: {record['plist']['PayloadUUID']} - {payload_name}: {payload_description}"
        }

    def check_indicators(self):
        if not self.indicators:
            return

        for result in self.results:
            if result["plist"].get("PayloadUUID"):
                payload_content = result["plist"]["PayloadContent"][0]

                # Alert on any known malicious configuration profiles in the indicator list.
                if self.indicators.check_profile(result["plist"]["PayloadUUID"]):
                    self.log.warning(f"Found a known malicious configuration profile \"{result['plist']['PayloadDisplayName']}\" with UUID '{result['plist']['PayloadUUID']}'.")
                    self.detected.append(result)
                    continue

                # Highlight suspicious configuration profiles which may be used to hide notifications.
                if payload_content["PayloadType"] in ["com.apple.notificationsettings"]:
                    self.log.warning(f"Found a potentially suspicious configuration profile \"{result['plist']['PayloadDisplayName']}\" with payload type '{payload_content['PayloadType']}'.")
                    self.detected.append(result)
                    continue

    def run(self):
        for conf_file in self._get_backup_files_from_manifest(domain=CONF_PROFILES_DOMAIN):
            conf_rel_path = conf_file["relative_path"]
            # Filter out all configuration files that are not configuration profiles.
            if not conf_rel_path or not os.path.basename(conf_rel_path).startswith("profile-"):
                continue

            conf_file_path = self._get_backup_file_from_id(conf_file["file_id"])
            if not conf_file_path:
                continue

            with open(conf_file_path, "rb") as handle:
                try:
                    conf_plist = plistlib.load(handle)
                except Exception:
                    conf_plist = {}

            if "SignerCerts" in conf_plist:
                conf_plist["SignerCerts"] = [b64encode(x) for x in conf_plist["SignerCerts"]]
            if "PushTokenDataSentToServerKey" in conf_plist:
                conf_plist["PushTokenDataSentToServerKey"] = b64encode(conf_plist["PushTokenDataSentToServerKey"])
            if "LastPushTokenHash" in conf_plist:
                conf_plist["LastPushTokenHash"] = b64encode(conf_plist["LastPushTokenHash"])
            if "PayloadContent" in conf_plist:
                for x in range(len(conf_plist["PayloadContent"])):
                    if "PERSISTENT_REF" in conf_plist["PayloadContent"][x]:
                        conf_plist["PayloadContent"][x]["PERSISTENT_REF"] = b64encode(conf_plist["PayloadContent"][x]["PERSISTENT_REF"])

            self.results.append({
                "File Name": "configration profiles",
                "file_id": conf_file["file_id"],
                "relative_path": conf_file["relative_path"],
                "domain": conf_file["domain"],
                "plist": "conf_plist",
                "install_date": convert_timestamp_to_iso(conf_plist.get("InstallDate")),
            })

        self.log.info("Extracted details about %d configuration profiles", len(self.results))
