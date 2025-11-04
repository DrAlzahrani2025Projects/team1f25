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
```http
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
