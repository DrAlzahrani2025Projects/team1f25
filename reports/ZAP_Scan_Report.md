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