**NETLOGON Specification and Limitation:**

1. Timestamp Format:
  1. **[FACT]** The logged Timestamp is in local-system time zone, not UTC.

**[Parser Implementation]**

1. By default, the time will be adjusted to UTC, assuming "Arab Standard Time" time zone which is equivalent to UTC+3.
2. However, the parser can take other time zones as argument and adjust the output to UTC accordingly.

  1. **[FACT]** The logged Timestamp only logs the month day and time as MM/DD HH:MM:SS

**[Parser Implementation]**

1. Can only parse the dates within One Year.

1. Multiple Logging modules
  1. **[FACT]** Multiple modules are logging on the Netlogon log

**[Parser Implementation]**

    1. Only the "LOGON" module is being parsed.
    2. Limited parsing to type of NTLM authentication records within the LOGON module

**Parser Specification and Documentation:**

![](RackMultipart20221212-1-651nes_html_4ba353bdbc92861b.png)

![](RackMultipart20221212-1-651nes_html_3a1bb75ceb27bdbf.png)
