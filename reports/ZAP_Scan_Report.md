# ⚡ ZAP by Checkmarx Scanning Report

**Site:** [http://localhost:5001](http://localhost:5001)  
**Generated on:** Mon, Nov 3, 2025 – 20:19:53  
**ZAP Version:** 2.16.1  
**Scanner:** ZAP by Checkmarx

---

## 🧾 Summary of Alerts

| Risk Level | Number of Alerts |
|-------------|------------------|
| **High** | 0 |
| **Medium** | 2 |
| **Low** | 2 |
| **Informational** | 3 |

---

## 🧩 Summary of Sequences
Each step indicates:  
**result (Pass/Fail)** – **risk (highest alert for the step, if any)**

---

## ⚠️ Alerts

### 🟠 Medium Risk

#### 1. Content Security Policy (CSP) Header Not Set
**Instances:** 3  
**URLs:**
- `http://localhost:5001/robots.txt`
- `http://localhost:5001/sitemap.xml`
- `http://localhost:5001/team1f25/`

**Description:**  
CSP helps detect and mitigate XSS and data-injection attacks. It allows the site to define trusted content sources for JavaScript, CSS, images, fonts, etc.

**Solution:**  
Configure your server or load balancer to set the `Content-Security-Policy` header.

**References:**  
- [MDN: CSP Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)  
- [OWASP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)  
- [W3C CSP Spec](https://www.w3.org/TR/CSP/)  
- [Web.dev CSP Overview](https://web.dev/articles/csp)

**CWE ID:** 693 | **WASC ID:** 15 | **Plugin ID:** 10038

---

#### 2. Missing Anti-Clickjacking Header
**Instances:** 1  
**URL:** `http://localhost:5001/team1f25/`

**Description:**  
The response does not protect against Clickjacking. Missing either a `Content-Security-Policy` (`frame-ancestors`) or an `X-Frame-Options` header.

**Solution:**  
Add either:
X-Frame-Options: DENY
or
Content-Security-Policy: frame-ancestors 'none'

If the page should only be framed by your own site, use:
X-Frame-Options: SAMEORIGIN

**References:**

* [MDN: X-Frame-Options Header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Frame-Options)

**CWE ID:** 1021
**WASC ID:** 15
**Plugin ID:** 10020

---

### 🟡 Low Risk

#### 3. Server Leaks Version Information via “Server” HTTP Response Header Field

**Instances:** 4

**URLs:**

* [http://localhost:5001/robots.txt](http://localhost:5001/robots.txt)
* [http://localhost:5001/sitemap.xml](http://localhost:5001/sitemap.xml)
* [http://localhost:5001/team1f25/](http://localhost:5001/team1f25/)
* [http://localhost:5001/team1f25/static/css/index.CIiu7Ygf.css](http://localhost:5001/team1f25/static/css/index.CIiu7Ygf.css)

**Evidence:** TornadoServer/6.5.2

**Description:**
The server leaks version information through the `Server` HTTP header, which can help attackers identify vulnerabilities.

**Solution:**
Suppress or sanitize the `Server` header to remove version information.

**References:**

* [Apache: ServerTokens Directive](https://httpd.apache.org/docs/current/mod/core.html#servertokens)
* [Microsoft Guidelines](https://learn.microsoft.com/en-us/previous-versions/msp-n-p/ff648552%28v=pandp.10%29)
* [Troy Hunt: Response Headers](https://www.troyhunt.com/shhh-dont-let-your-response-headers/)

**CWE ID:** 497
**WASC ID:** 13
**Plugin ID:** 10036

---

#### 4. X-Content-Type-Options Header Missing

**Instances:** 2

**URLs:**

* [http://localhost:5001/team1f25/](http://localhost:5001/team1f25/)
* [http://localhost:5001/team1f25/static/css/index.CIiu7Ygf.css](http://localhost:5001/team1f25/static/css/index.CIiu7Ygf.css)

**Description:**
The **X-Content-Type-Options** header was not set to `nosniff`. Without it, older browsers might MIME-sniff and misinterpret responses as another type.

**Solution:**
Add the following header to all responses:
X-Content-Type-Options: nosniff

**References:**

* [Microsoft Docs](https://learn.microsoft.com/en-us/previous-versions/windows/internet-explorer/ie-developer/compatibility/gg622941%28v=vs.85%29)
* [OWASP Security Headers](https://owasp.org/www-community/Security_Headers)

**CWE ID:** 693
**WASC ID:** 15
**Plugin ID:** 10021

---

### ℹ️ Informational Alerts

#### 5. Modern Web Application

**Instances:** 1
**URL:** [http://localhost:5001/team1f25/](http://localhost:5001/team1f25/)
**Evidence:** `<script> window.prerenderReady = false </script>`

**Description:**
The application behaves as a modern web app or single-page app (SPA) with dynamic rendering.

**Solution:** None required.
**Plugin ID:** 10109

---

#### 6. Tech Detected – TornadoServer

**Instances:** 1
**URL:** [http://localhost:5001/team1f25/static/css/index.CIiu7Ygf.css](http://localhost:5001/team1f25/static/css/index.CIiu7Ygf.css)
**Evidence:** TornadoServer/6.5.2

**Description:**
Detected TornadoServer technology (version 6.5.2).

**Solution:** Informational only.

**Reference:** [Tornado Web Framework](https://tornadoweb.org)
**WASC ID:** 13
**Plugin ID:** 10004

---

#### 7. User Agent Fuzzer

**Instances:** 12
**URL Tested:** [http://localhost:5001/team1f25/](http://localhost:5001/team1f25/)

**Description:**
Checked for differences in responses based on various User-Agent headers (e.g., IE, Chrome, Firefox, Googlebot, Yahoo Slurp, MSNBOT).

**Solution:** Informational only — ensure consistent handling for all User-Agents.

**Reference:** [OWASP Web Security Testing Guide](https://owasp.org/wstg)
**Plugin ID:** 10104

---