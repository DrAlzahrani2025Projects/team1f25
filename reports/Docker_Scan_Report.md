# Docker Scan Vulnerability Report

**Date:** Tue Nov  4 23:12:18 UTC 2025
**Git SHA:** e24db880139dc068eb56f8007d7b8ec92130420c
**Branch/Ref:** main
**Scanner:** Trivy

## Image Scanned
`local/team1f25-streamlit:e24db880139dc068eb56f8007d7b8ec92130420c`

## Summary of Vulnerabilities

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 0 |
| 🟠 HIGH | 0 |
| 🟡 MEDIUM | 2 |
| 🔵 LOW | 51 |
| ⚪ UNKNOWN | 0 |
| **TOTAL** | **53** |

## Vulnerability Details

| Severity | CVE | Package | Version | Fixed In | Title |
|---|---|---|---|---|---|
| MEDIUM | CVE-2025-8869 | pip | 25.0.1 | 25.3 | pip: pip missing checks on symbolic link extraction |
| MEDIUM | CVE-2025-7709 | libsqlite3-0 | 3.46.1-7 | not fixed | An integer overflow exists in the  FTS5 https://sqlite.org/fts5.html e ... |
| LOW | CVE-2022-0563 | util-linux | 2.41-5 | not fixed | util-linux: partial disclosure of arbitrary files in chfn and chsh when compiled |
| LOW | TEMP-0290435-0B57B5 | tar | 1.35+dfsg-3.1 | not fixed | [tar's rmt command may have undesired side effects] |
| LOW | CVE-2005-2541 | tar | 1.35+dfsg-3.1 | not fixed | tar: does not properly warn the user when extracting setuid or setgid files |
| LOW | TEMP-0517018-A83CE6 | sysvinit-utils | 3.14-4 | not fixed | [sysvinit: no-root option in expert installer exposes locally exploitable securi |
| LOW | CVE-2011-4116 | perl-base | 5.40.1-6 | not fixed | perl: File:: Temp insecure temporary file handling |
| LOW | TEMP-0628843-DBAD28 | passwd | 1:4.17.4-2 | not fixed | [more related to CVE-2005-4890] |
| LOW | CVE-2024-56433 | passwd | 1:4.17.4-2 | not fixed | shadow-utils: Default subordinate ID configuration in /etc/login.defs could lead |
| LOW | CVE-2007-5686 | passwd | 1:4.17.4-2 | not fixed | initscripts in rPath Linux 1 sets insecure permissions for the /var/lo ... |
| LOW | CVE-2025-6141 | ncurses-bin | 6.5+20250216-2 | not fixed | gnu-ncurses: ncurses Stack Buffer Overflow |
| LOW | CVE-2025-6141 | ncurses-base | 6.5+20250216-2 | not fixed | gnu-ncurses: ncurses Stack Buffer Overflow |
| LOW | CVE-2022-0563 | mount | 2.41-5 | not fixed | util-linux: partial disclosure of arbitrary files in chfn and chsh when compiled |
| LOW | TEMP-0628843-DBAD28 | login.defs | 1:4.17.4-2 | not fixed | [more related to CVE-2005-4890] |
| LOW | CVE-2024-56433 | login.defs | 1:4.17.4-2 | not fixed | shadow-utils: Default subordinate ID configuration in /etc/login.defs could lead |
| LOW | CVE-2007-5686 | login.defs | 1:4.17.4-2 | not fixed | initscripts in rPath Linux 1 sets insecure permissions for the /var/lo ... |
| LOW | CVE-2022-0563 | login | 1:4.16.0-2+really2.41-5 | not fixed | util-linux: partial disclosure of arbitrary files in chfn and chsh when compiled |
| LOW | CVE-2022-0563 | libuuid1 | 2.41-5 | not fixed | util-linux: partial disclosure of arbitrary files in chfn and chsh when compiled |
| LOW | CVE-2023-31439 | libudev1 | 257.8-1~deb13u2 | not fixed | An issue was discovered in systemd 253. An attacker can modify the con ... |
| LOW | CVE-2023-31438 | libudev1 | 257.8-1~deb13u2 | not fixed | An issue was discovered in systemd 253. An attacker can truncate a sea ... |
| LOW | CVE-2023-31437 | libudev1 | 257.8-1~deb13u2 | not fixed | An issue was discovered in systemd 253. An attacker can modify a seale ... |
| LOW | CVE-2013-4392 | libudev1 | 257.8-1~deb13u2 | not fixed | systemd: TOCTOU race condition when updating file permissions and SELinux securi |
| LOW | CVE-2025-6141 | libtinfo6 | 6.5+20250216-2 | not fixed | gnu-ncurses: ncurses Stack Buffer Overflow |
| LOW | CVE-2023-31439 | libsystemd0 | 257.8-1~deb13u2 | not fixed | An issue was discovered in systemd 253. An attacker can modify the con ... |
| LOW | CVE-2023-31438 | libsystemd0 | 257.8-1~deb13u2 | not fixed | An issue was discovered in systemd 253. An attacker can truncate a sea ... |
| LOW | CVE-2023-31437 | libsystemd0 | 257.8-1~deb13u2 | not fixed | An issue was discovered in systemd 253. An attacker can modify a seale ... |
| LOW | CVE-2013-4392 | libsystemd0 | 257.8-1~deb13u2 | not fixed | systemd: TOCTOU race condition when updating file permissions and SELinux securi |
| LOW | CVE-2021-45346 | libsqlite3-0 | 3.46.1-7 | not fixed | sqlite: crafted SQL query allows a malicious user to obtain sensitive informatio |
| LOW | CVE-2022-0563 | libsmartcols1 | 2.41-5 | not fixed | util-linux: partial disclosure of arbitrary files in chfn and chsh when compiled |
| LOW | CVE-2025-6141 | libncursesw6 | 6.5+20250216-2 | not fixed | gnu-ncurses: ncurses Stack Buffer Overflow |
| LOW | CVE-2022-0563 | libmount1 | 2.41-5 | not fixed | util-linux: partial disclosure of arbitrary files in chfn and chsh when compiled |
| LOW | CVE-2022-0563 | liblastlog2-2 | 2.41-5 | not fixed | util-linux: partial disclosure of arbitrary files in chfn and chsh when compiled |
| LOW | CVE-2019-9192 | libc6 | 2.41-12 | not fixed | glibc: uncontrolled recursion in function check_dst_limits_calc_pos_1 in posix/r |
| LOW | CVE-2019-1010025 | libc6 | 2.41-12 | not fixed | glibc: information disclosure of heap addresses of pthread_created thread |
| LOW | CVE-2019-1010024 | libc6 | 2.41-12 | not fixed | glibc: ASLR bypass using cache of thread stack and heap |
| LOW | CVE-2019-1010023 | libc6 | 2.41-12 | not fixed | glibc: running ldd on malicious ELF leads to code execution because of wrong siz |
| LOW | CVE-2019-1010022 | libc6 | 2.41-12 | not fixed | glibc: stack guard protection bypass |
| LOW | CVE-2018-20796 | libc6 | 2.41-12 | not fixed | glibc: uncontrolled recursion in function check_dst_limits_calc_pos_1 in posix/r |
| LOW | CVE-2010-4756 | libc6 | 2.41-12 | not fixed | glibc: glob implementation can cause excessive CPU and memory consumption due to |
| LOW | CVE-2019-9192 | libc-bin | 2.41-12 | not fixed | glibc: uncontrolled recursion in function check_dst_limits_calc_pos_1 in posix/r |
| LOW | CVE-2019-1010025 | libc-bin | 2.41-12 | not fixed | glibc: information disclosure of heap addresses of pthread_created thread |
| LOW | CVE-2019-1010024 | libc-bin | 2.41-12 | not fixed | glibc: ASLR bypass using cache of thread stack and heap |
| LOW | CVE-2019-1010023 | libc-bin | 2.41-12 | not fixed | glibc: running ldd on malicious ELF leads to code execution because of wrong siz |
| LOW | CVE-2019-1010022 | libc-bin | 2.41-12 | not fixed | glibc: stack guard protection bypass |
| LOW | CVE-2018-20796 | libc-bin | 2.41-12 | not fixed | glibc: uncontrolled recursion in function check_dst_limits_calc_pos_1 in posix/r |
| LOW | CVE-2010-4756 | libc-bin | 2.41-12 | not fixed | glibc: glob implementation can cause excessive CPU and memory consumption due to |
| LOW | CVE-2022-0563 | libblkid1 | 2.41-5 | not fixed | util-linux: partial disclosure of arbitrary files in chfn and chsh when compiled |
| LOW | CVE-2011-3374 | libapt-pkg7.0 | 3.0.3 | not fixed | It was found that apt-key in apt, all versions, do not correctly valid ... |
| LOW | CVE-2025-5278 | coreutils | 9.7-3 | not fixed | coreutils: Heap Buffer Under-Read in GNU Coreutils sort via Key Specification |
| LOW | CVE-2017-18018 | coreutils | 9.7-3 | not fixed | coreutils: race condition vulnerability in chown and chgrp |
| LOW | CVE-2022-0563 | bsdutils | 1:2.41-5 | not fixed | util-linux: partial disclosure of arbitrary files in chfn and chsh when compiled |
| LOW | TEMP-0841856-B18BAF | bash | 5.2.37-2+b5 | not fixed | [Privilege escalation possible to other user than root] |
| LOW | CVE-2011-3374 | apt | 3.0.3 | not fixed | It was found that apt-key in apt, all versions, do not correctly valid ... |

---
_Generated automatically by Trivy vulnerability scanner_
