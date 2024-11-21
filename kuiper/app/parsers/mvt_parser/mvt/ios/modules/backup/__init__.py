# Mobile Verification Toolkit (MVT)
# Copyright (c) 2021 The MVT Project Authors.
# Use of this software is governed by the MVT License 1.1 that can be found at
#   https://license.mvt.re/1.1/

from .backup_info import BackupInfo
from .installed_app import InstalledApplications
from .configuration_profiles import ConfigurationProfiles
from .manifest import Manifest
from .profile_events import ProfileEvents



BACKUP_MODULES = [BackupInfo, Manifest, ProfileEvents, InstalledApplications, ConfigurationProfiles]