#!C:\Python24\python.exe


"""A module for translating and manipulating SDDL strings.


    SDDL strings are used by Microsoft to describe ACLs as described in
    http://msdn.microsoft.com/en-us/library/aa379567.aspx.

    Example: D:(A;;CCLCSWLOCRRC;;;AU)(A;;CCLCSWRPLOCRRC;;;PU)
    """

__author__ = 'tojo2000@tojo2000.com (Tim Johnson)'
__version__ = '0.1'
__updated__ = '2008-07-14'

import re
import os

# Using API functions from the pywin32 package is MUCH faster than WMI
if os.name == 'nt':
    from win32security import LookupAccountSid,GetBinarySid

re_valid_string = re.compile('^[ADO][ADLU]?\:\(.*\)$')
re_perms = re.compile('\(([^\(\)]+)\)')
re_type = re.compile('^[DOGS](?!:\\\)')
re_owner = re.compile('^O:[^:()]+(?=[DGS]:)')
re_group = re.compile('G:[^:()]+(?=[DOS]:)')
re_acl = re.compile('[DS]:.+$')
re_dacl = re.compile('[D]:.+\)(?=S)|[D]:.+$')
re_sacl = re.compile('[S]:.+\)(?=D)|[S]:.+$')
re_acl_flags = re.compile('[DS]:(?!\()(.+?)\(')
re_flags = ('(AI|AR|P|NO_ACCESS_CONTROL)')
re_const = re.compile('(\w\w)')
re_non_acl = re.compile('[^:()]+$')

SDDL_TYPE = {'O': 'Owner',
                         'G': 'Group',
                         'D': 'DACL',
                         'S': 'SACL'}

ACL_FLAGS = {'P': 'PROTECTED',
                         'AR': 'AUTO_INHERIT_REQ',
                         'AI': 'AUTO_INHERITED',
                         'NO_ACCESS_CONTROL': 'NULL_ACL'}

ACE_TYPE = {'A' : 'ACCESS_ALLOWED',
                    'D' : 'ACCESS_DENIED',
                    'OA': 'ACCESS_ALLOWED_OBJECT',
                    'OD': 'ACCESS_DENIED_OBJECT',
                    'AU': 'SYSTEM_AUDIT',
                    'AL': 'SYSTEM_ALARM',
                    'OU': 'SYSTEM_AUDIT_OBJECT',
                    'OL': 'SYSTEM_ALARM_OBJECT',
                    'ML': 'STSTEM_MANDITORY_LABEL',
                    'XA': 'ACCESS_ALLOWED_CALLBACK',
                    'XD': 'ACCESS_DENIED_CALLBACK',
                    'RA': 'SYSTEM_RESOURCE_ATTRIBUTE',
                    'SP': 'SYSTEM_SCOPED_POLICY_ID',
                    'XU': 'SYSTEM AUDIT_CALLBACK',
                    'ZA': 'ACCESS_ALLOWED_CALLBACK'}

ACE_FLAGS = {'CI': 'CONTAINER_INHERIT',
                    'OI': 'OBJECT_INHERIT',
                    'NP': 'NO_PROPAGATE_INHERIT',
                    'IO': 'INHERIT_ONLY',
                    'ID': 'INHERITED',
                    'SA': 'SUCCESSFUL_ACCESS',
                    'FA': 'FAILED_ACCESS'}

ACCESS = {# Generic Access Rights
                    'GA': 'GENERIC_ALL',
                    'GR': 'GENERIC_READ',
                    'GW': 'GENERIC_WRITE',
                    'GX': 'GENERIC_EXECUTE',

                    # Standard Access Rights
                    'RC': 'READ_CONTROL',
                    'SD': 'DELETE',
                    'WD': 'WRITE_DAC',
                    'WO': 'WRITE_OWNER',

                    # Directory Service Object Access Rights
                    'RP': 'DS_READ_PROP',
                    'WP': 'DS_WRITE_PROP',
                    'CC': 'DS_CREATE_CHILD',
                    'DC': 'DS_DELETE_CHILD',
                    'LC': 'DS_LIST',
                    'SW': 'DS_SELF',
                    'LO': 'DS_LIST_OBJECT',
                    'DT': 'DS_DELETE_TREE',
                    'CR': 'DS_CONTROL_ACCESS',

                    # File Access Rights
                    'FA': 'FILE_ALL_ACCESS',
                    'FR': 'FILE_GENERIC_READ',
                    'FW': 'FILE_GENERIC_WRITE',
                    'FX': 'FILE_GENERIC_EXECUTE',

                    # Registry Access Rights
                    'KA': 'KEY_ALL_ACCESS',
                    'KR': 'KEY_READ',
                    'KW': 'KEY_WRITE',
                    'KX': 'KEY_EXECUTE',
                    
                    #Manditory Label Rights
                    'NR': 'NO_READ_UP',
                    'NW': 'NO_WRITE_UP',
                    'NX': 'NO_EXECUTE_UP'}


"""
        Access Mask: 32-bits
         ___________________________________
        | Bit(s)  | Meaning                 |
         -----------------------------------
        | 0 - 15  | Object Access Rights    |
        | 16 - 22 | Standard Access Rights  |
        | 23      | Can access security ACL |
        | 24 - 27 | Reserved                |
        | 28 - 31 | Generic Access Rights   |
         -----------------------------------
"""
ACCESS_HEX = {
                    # Generic Access Rights
                    0x10000000: 'GA',
                    0x20000000: 'GX',
                    0x40000000: 'GW',
                    0x80000000: 'GR',

                    # Standard Access Rights
                    0x00010000: 'SD',
                    0x00020000: 'RC',
                    0x00040000: 'WD',
                    0x00080000: 'WO',

                    # Object Access Rights
                    0x00000001: 'CC',
                    0x00000002: 'DC',
                    0x00000004: 'LC',
                    0x00000008: 'SW',
                    0x00000010: 'RP',
                    0x00000020: 'WP',
                    0x00000040: 'DT',
                    0x00000080: 'LO',
                    0x00000100: 'CR'}


TRUSTEE = {'AC': 'ALL APPLICATION PACKAGES',
                     'AN': 'Anonymous',
                     'AO': 'Account Operators',
                     'AU': 'Authenticated Users',
                     'BA': 'Administrators',
                     'BG': 'Guests',
                     'BO': 'Backup Operators',
                     'BU': 'Users',
                     'CA': 'Certificate Publishers',
                     'CD': 'Certificate Services DCOM Access',
                     'CG': 'Creator Group',
                     'CO': 'Creator Owner',
                     'DA': 'Domain Admins',
                     'DC': 'Domain Computers',
                     'DD': 'Domain Controllers',
                     'DG': 'Domain Guests',
                     'DU': 'Domain Users',
                     'EA': 'Enterprise Admins',
                     'ED': 'Enterprise Domain Controllers',
                     'HI': 'High Integrity',
                     'IU': 'Interactive Users',
                     'LA': 'Local Administrator',
                     'LG': 'Local Guest',
                     'LS': 'Local Service',
                     'LW': 'Low Integrity',
                     'ME': 'Medium Integrity',
                     'MU': 'Perfmon Users',
                     'NO': 'Network Configuration Operators',
                     'NS': 'Network Service',
                     'NU': 'Network',
                     'PA': 'Group Policy Admins',
                     'PO': 'Printer Operators',
                     'PS': 'Self',
                     'PU': 'Power Users',
                     'RC': 'Restricted Code',
                     'RD': 'Remote Desktop Users',
                     'RE': 'Replicator',
                     'RO': 'Enterprise Read-Only Domain Controllers',
                     'RS': 'RAS Servers',
                     'RU': 'Pre-Win2k Compatibility Access',
                     'SA': 'Schema Administrators',
                     'SI': 'System Integrity',
                     'SO': 'Server Operators',
                     'SU': 'Service',
                     'SY': 'Local System',
                     'WD': 'Everyone'
                     }


class Error(Exception):
    """Generic Error class."""


class InvalidSddlStringError(Error):
    """The input string provided was not a valid SDDL string."""


class InvalidSddlTypeError(Error):
    """The type specified must be O, G, D, or S."""


class InvalidAceStringError(Error):
    """The ACE string provided was invalid."""


def TranslateSid(sid_string):
    """Translate a SID string to an account name.

    Args:
        sid_string: a SID in string form

    Returns:
        A string with the account name if the name resolves.
        None if the name is not found.
    """
    if os.name == 'nt':
        try:
            account = LookupAccountSid(None, GetBinarySid(sid_string))
        except:
            account = None

    if account:
        if len(account[1]):
            return account[1] + '\\' + account[0]
        else:
            return account[0]


def SortAceByTrustee(x, y):
    """Custom sorting function to sort SDDL.ACE objects by trustee.

    Args:
        x: first object being compared
        y: second object being compared

    Returns:
        The results of a cmp() between the objects.
    """
    return cmp(x.trustee, y.trustee)


def AccessFromHex(hex):
    """Convert a hex access rights specifier to it's string equivalent.

    Args:
        hex: The hexadecimal string to be converted

    Returns:
        A string containing the converted access rights
    """
    hex = int(hex, 16)
    rights = ""

    for spec in ACCESS_HEX.items():
        if hex & spec[0]:
            rights += spec[1]

    return rights


class ACE(object):
    """Represents an access control entry."""

    def __init__(self, ace_string):
        """Initializes the SDDL::ACE object.

        Args:
            ace_string: a string representing a single access control entry
            access_constants: a dictionary of access constants for translation

        Raises:
            InvalidAceStringError: If the ace string provided doesn't appear to be
                valid.
        """
        self.ace_string = ace_string
        self.flags = []
        self.perms = []
        fields = ace_string.split(';')

        if len(fields) != 6:
            raise InvalidAceStringError

        if (ACE_TYPE[fields[0]]):
            self.ace_type = ACE_TYPE[fields[0]]
        else:
            self.ace_type = fields[0]

        for flag in re.findall(re_const, fields[1]):
            if ACE_FLAGS[flag]:
                self.flags.append(ACE_FLAGS[flag])
            else:
                self.flags.append(flag)

        if fields[2][0:2] == '0x':    # If specified in hex
            fields[2] = AccessFromHex(fields[2])

        for perm in re.findall(re_const, fields[2]):
            if ACCESS[perm]:
                self.perms.append(ACCESS[perm])
            else:
                self.perms.append(perm)

        self.perms.sort()
        self.object_type = fields[3]
        self.inherited_type = fields[4]
        self.sid = fields[5]
        self.trustee = None

        if TRUSTEE.__contains__(fields[5]):
            self.trustee = TRUSTEE[fields[5]]
        
        if os.name == 'nt':
            if not self.trustee:
                self.trustee = TranslateSid(fields[5])

        if not self.trustee:
            self.trustee = 'Unknown or invalid SID.'


class SDDL(object):
    """Represents an SDDL string."""

    def __init__(self, sddl_string, target=None):
        """Initializes the SDDL object.

        Args:
            input_string: The SDDL string representation of the ACL
            target: Some values of the SDDL string change their meaning depending
                on the type of object they describe.
                Note:    The only supported type right now is 'service'

        Raises:
            SDDLInvalidStringError: if the string doesn't appear to be valid
        """
        self.target = target
        self.sddl_string = sddl_string
        self.sddl_type = None
        self.sddl_dacl = None
        self.sddl_sacl = None
        self.acl = []
        self.dacl = []
        self.sacl = []
        self.dacl_flags = []
        self.sacl_flags = []
        sddl_owner_part = re.search(re_owner, sddl_string)
        sddl_group_part = re.search(re_group, sddl_string)
        sddl_acl_part = re.search(re_acl, sddl_string)
        sddl_dacl_part = re.search(re_dacl, sddl_string)
        sddl_sacl_part = re.search(re_sacl, sddl_string)
        self.ACCESS = ACCESS
        self.group_sid = None
        self.group_account = None
        self.owner_sid = None
        self.owner_account = None

        if self.target == 'service':
            self.ACCESS['CC'] = 'Query Configuration'
            self.ACCESS['DC'] = 'Change Configuration'
            self.ACCESS['LC'] = 'Query State'
            self.ACCESS['SW'] = 'Enumerate Dependencies'
            self.ACCESS['RP'] = 'Start'
            self.ACCESS['WP'] = 'Stop'
            self.ACCESS['DT'] = 'Pause'
            self.ACCESS['LO'] = 'Interrogate'
            self.ACCESS['CR'] = 'User Defined'
            self.ACCESS['SD'] = 'Delete'
            self.ACCESS['RC'] = 'Read the Security Descriptor'
            self.ACCESS['WD'] = 'Change Permissions'
            self.ACCESS['WO'] = 'Change Owner'

        for match in (sddl_owner_part, sddl_group_part, sddl_dacl_part, sddl_sacl_part):
            try:
                part = match.group()
                sddl_prefix = re.match(re_type, part).group()
            except:
                part = ''
                pass
#            sddl_prefix = re.match(re_type, part).group()
                    
            if (sddl_prefix == 'D'):
                self.sddl_dacl = SDDL_TYPE[sddl_prefix]
                dacl_flags = re.search(re_acl_flags, part)
                if dacl_flags is not None:
                    for flag in re.findall(re_flags, dacl_flags.group(1)):
                        if ACL_FLAGS[flag]:
                            self.dacl_flags.append(ACL_FLAGS[flag])
                for perms in re.findall(re_perms, part):
                    self.dacl.append(ACE(perms))
                    
            elif (sddl_prefix == 'S'):
                self.sddl_sacl = SDDL_TYPE[sddl_prefix]
                sacl_flags = re.search(re_acl_flags, part)
                if sacl_flags is not None:
                    for flag in re.findall(re_flags, sacl_flags.group(1)):
                        if ACL_FLAGS[flag]:
                            self.sacl_flags.append(ACL_FLAGS[flag])
                for perms in re.findall(re_perms, part):
                    self.sacl.append(ACE(perms))

            elif (sddl_prefix == 'G'):
                self.group_sid = re.search(re_non_acl, part).group()

                if self.group_sid in TRUSTEE:
                    self.group_account = TRUSTEE[self.group_sid]
                else:
                    if os.name == 'nt':
                        self.group_account = TranslateSid(self.group_sid)

                if not self.group_account:
                    self.group_account = 'Unknown'

            elif (sddl_prefix == 'O'):
                self.owner_sid = re.search(re_non_acl, part).group()

                if self.owner_sid in TRUSTEE:
                    self.owner_account = TRUSTEE[self.owner_sid]
                else:
                    if os.name == 'nt':
                        self.owner_account = TranslateSid(self.owner_sid)

                if not self.owner_account:
                    self.owner_account = 'Unknown'

            else:
                raise InvalidSddlStringError