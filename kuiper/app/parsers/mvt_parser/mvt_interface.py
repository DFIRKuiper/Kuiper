import os
import sys
import subprocess
import json
import io
import os


def auto_interface(file, parser):
    modules=["ios_BackupInfo",
                "ios_Manifest",
                "ios_ProfileEvents",
                "ios_InstalledApplications",
                "ios_Calls",
                "ios_ChromeFavicon",
                "ios_ChromeHistory",
                "ios_Contacts",
                "ios_FirefoxFavicon",
                "ios_FirefoxHistory",
                "ios_IDStatusCache",
                "ios_InteractionC",
                "ios_LocationdClients",
                "ios_OSAnalyticsADDaily",
                "ios_Datausage",
                "ios_SafariBrowserState",
                "ios_SafariHistory",
                "ios_TCC",
                "ios_SMS",
                "ios_SMSAttachments",
                "ios_WebkitResourceLoadStatistics",
                "ios_WebkitSessionResourceLog",
                "ios_Whatsapp",
                "ios_Shortcuts",
                "ios_Timeline",
                "ios_ConfigurationProfiles"
                ]
    try:
        if parser in modules:
            parser = parser.lstrip("ios_")
            CurrentPath     = os.path.dirname(os.path.abspath(__file__))
            file = os.path.dirname(file)
            cmd = 'cd '+CurrentPath+'/ && python3 -m mvt.ios.cli check-backup -m '+parser+' -o ./ '+file
            proc = subprocess.Popen(
                cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            res, err = proc.communicate()
            if err != b'' and err != "":
                raise Exception(err)

            res = res.split(b"\n")
            data = []
            for line in res:
                if line.startswith(b"{") and line.endswith(b"}"):
                    data.append(json.loads(line))
            return data

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = parser + " Parser: " + \
            str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return(None , msg)



if __name__ == "__main__":
    r = auto_interface("/app/app/newbackup/mdf_iPhone_decrypted", "ios_SMS")
    print ((r))



