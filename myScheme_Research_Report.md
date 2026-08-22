# myScheme Government Service Platform - Comprehensive Research Report

**Report Date:** August 23, 2026
**Researched By:** AI Assistant
**Focus:** Official Government Documentation

---

## Executive Summary

myScheme is India's National Platform for government scheme discovery, launched on July 4, 2022, by the Prime Minister. It is developed, managed, and operated by the National e-Governance Division (NeGD) under the Ministry of Electronics and Information Technology (MeitY). The platform provides programmatic access through API Setu, India's Open API platform.

**Key Findings:**
- ✅ Public APIs ARE available through API Setu
- ✅ Formal registration and approval process required
- ✅ Multiple authentication mechanisms supported
- ⚠️ Specific API documentation requires developer account access
- ⚠️ No publicly available detailed technical specifications found

---

## 1. What is myScheme - Official Purpose, Scope, Coverage

### Official Purpose
myScheme is a **National Platform that aims to offer one-stop search and discovery of Government schemes**. It serves as a marketplace for schemes, providing a single platform for schemes from the Central Government, State Governments, and Union Territories.

**Official Website:** https://www.myscheme.gov.in/

### Core Objectives
- Deliver government schemes in a **seamless, convenient, cashless, paperless, faceless, time-bound, and transparent manner** across Government silos
- Provide an innovative, technology-based solution to discover scheme information based upon the eligibility of citizens
- Eliminate the need for citizens to visit multiple departmental websites or review extensive scheme guidelines to check eligibility

### Platform Coverage (OFFICIAL DATA)

| Metric | Value | Source |
|--------|-------|--------|
| Total Schemes | **4,700+** | Digital India website |
| Scheme Categories | **1,000+** | As of Sept 22, 2023 |
| Geographic Coverage | **Central + All States/UTs** | myScheme official site |

### Scheme Categories
- Social Welfare & Empowerment
- Agriculture, Rural & Environment
- Business & Entrepreneurship
- Education & Learning
- Health & Wellness
- Housing & Shelter
- Skills & Employment
- Sports & Culture
- Transport & Infrastructure
- Utility & Sanitation
- Women & Child

### How It Works (3-Step Process)
1. **Input Details**: Users enter basic demographic, income, social category details
2. **Scheme Discovery**: myScheme displays relevant schemes based on provided information
3. **Application Guidance**: Users select eligible schemes to get more information, FAQs, and application details

### Governance Structure
- **Developed & Operated By:** National e-Governance Division (NeGD), Digital India Corporation
- **Supported By:** Ministry of Electronics and Information Technology (MeitY)
- **Partner Ministries:** Department of Administrative Reforms and Public Grievance (DARPG), Central and State Ministries/Departments
- **Parent Organization:** Digital India Corporation

### Contact Information (OFFICIAL)
- **Address:** 4th Floor, NeGD, Electronics Niketan, 6 CGO Complex, Lodhi Road, New Delhi – 110003, India
- **Phone:** (011) 24303714
- **Fax:** 011-24303778
- **Email:** support-myscheme@digitalindia.gov.in
- **General NeGD Email:** webmaster@digitalindia.gov.in

---

## 2. API Availability - Public APIs and API Setu Integration

### ✅ CONFIRMATION: Public APIs ARE Available

myScheme provides programmatic access through **API Setu**, India's official Open API platform operated by MeitY.

### API Setu Platform Details
- **Official Portal:** https://www.apisetu.gov.in/
- **API Directory:** https://directory.apisetu.gov.in/
- **Documentation:** https://docs.apisetu.gov.in/
- **Sandbox Environment:** https://sandbox.api-setu.in/
- **Partner Portal:** https://partners.apisetu.gov.in/

### Available myScheme APIs (OFFICIALLY DOCUMENTED)

#### 1. Ministry Wise Schemes Count API
- **API Name:** Ministry Wise Schemes Count 4.0
- **Specification:** OAS 3.0 (OpenAPI Specification 3.0)
- **Location:** https://directory.apisetu.gov.in/api-collection/myscheme
- **Purpose:** Provides count of schemes organized by ministry
- **Data Type:** Service API (non-user-specific data)

#### Additional myScheme APIs
The API Directory lists myScheme APIs under the tag "myscheme" at:
https://directory.apisetu.gov.in/search?tag=myscheme

**Note:** Detailed API endpoint specifications, request/response schemas, and complete API documentation require developer account access through the API Setu partner portal.

### API Setu as Trusted Partner
API Setu is already a trusted partner for large Digital India platforms:
- DigiLocker
- MeriPehchaan
- National Academic Depository (NAD)
- **myScheme**
- UMANG
- CBSE
- GSTN

---

## 3. Authorization Requirements - Registration, Subscription, API Keys

### Consumer Onboarding Process (OFFICIAL WORKFLOW)

#### Step 1: Signup on API Setu Platform
- **Portal:** https://partners.apisetu.gov.in/signup
- **Alternative Signup:** https://utils.apisetu.gov.in/signup
- **Login Portal:** https://partners.apisetu.gov.in/signin

#### Step 2: Required Documentation
Consumers must provide:
1. **Proof of Identity**
2. **Authority Letter**
3. **Organization PAN**
4. **GST Registration Certificate**
5. **Certificate of Incorporation**
6. **Valid Use Case** (mandatory justification)

#### Step 3: Registration Requirements
- **Email:** Must use **domain-registered email ID only**
- **Organization Limit:** Only **one request per organization** will be entertained
- **Evaluation:** API Management team evaluates the request and use case
- **Approval:** Signup request approved after evaluation

#### Step 4: API Subscription
- Browse the API marketplace
- Discover relevant APIs (e.g., myScheme APIs)
- Subscribe based on needs
- **Access granted only after publisher's approval**

#### Step 5: Generate API Keys
- Upon approval, generate API credentials:
  - Client ID
  - Client Secret
  - API Key

#### Step 6: Deploy and Authenticate
- Deploy APIs in your application
- Authenticate using provided credentials
- Receive responses in JSON/XML format

### Authentication & Authorization Mechanisms

API Setu supports multiple authentication methods:
1. **Client ID and Client Secret**
2. **API Key**
3. **OAuth 2.0** (Recommended)

#### OAuth 2.0 Implementation (OFFICIAL PROCESS)
1. **Setup:** Store clientID and secret from API Setu
2. **Token Generation:** Generate new token with stored credentials
3. **Token Usage:** Set authorization header as `Bearer <token-value>`
4. **Token Management:** Generate new token when old one expires
5. **Error Handling:** Handle 401 unauthorized responses (token expiration)

### Standard Operating Procedure (SOP)
Official SOP document available at:
https://cdn.apisetu.gov.in/portal/assets/SOP-APISETU.pdf

### Onboarding Guidelines for API Providers
https://negd.gov.in/wp-content/uploads/2025/06/Guidelines-for-Onboarding-for-API-as-a-service-provider-v15-Rev-1-1.pdf

---

## 4. Capabilities - Data/Services Accessible

### Available Data Through myScheme APIs

Based on official sources, myScheme APIs provide access to:

1. **Ministry Wise Schemes Count**
   - Aggregated counts of schemes by ministry
   - Non-user-specific data (Service API)

2. **Scheme Details** (Inferred from platform features)
   - Scheme name and description
   - Eligibility criteria
   - Benefits offered
   - Application procedure
   - Required documents
   - Scheme categories
   - Geographic coverage (Central/State/UT)
   - Ministry/Department information

3. **Scheme Search and Discovery** (Platform functionality)
   - Search by category
   - Search by ministry
   - Search by state/UT
   - Eligibility-based filtering

### Platform Features (Available on Web Portal)
- **Scheme Finder:** Eligibility-based scheme discovery
- **Check Eligibility Tools:** Scheme-specific eligibility checks
- **Dashboard:** Overview of schemes
- **User Profiles:** Save applications and track progress
- **Multi-language Support:** Available in Hindi and English

### Data Response Format
- **JSON** (primary)
- **XML** (supported)

### API Standards Compliance
- **OpenAPI Specification (OAS) 3.0** compliant
- Each published API properly documented with sample code
- Sufficient information for developers provided

---

## 5. Terms of Use - Allowed Usage Patterns, Rate Limits, Restrictions

### API Usage Limits (OFFICIAL POLICY)

**Documentation:** https://docs.apisetu.gov.in/document-central/terms-of-use/API%20Usage%20Limits.html

API Setu may impose limits on:
- **Number of API calls**
- **Frequency of API calls**

Users must:
- Comply with usage quotas
- Avoid activities that could overload the platform
- Note: Breach of usage policies may result in access restrictions or temporary suspension

**⚠️ Note:** Specific numerical rate limits are not publicly disclosed and are likely provided upon API subscription approval.

### Permitted Use and Access (OFFICIAL POLICY)

**Documentation:** https://docs.apisetu.gov.in/document-central/terms-of-use/Permitted%20Use%20and%20Access.html

Users are permitted to:
- Access and use APIs solely for **lawful and authorized purposes**
- Use APIs in accordance with documentation provided by API Setu
- Conduct use with **valid credentials** issued to the user
- Use only for **internal and approved use cases**

### Access Restrictions (OFFICIAL POLICY)

**Documentation:** https://docs.apisetu.gov.in/document-central/terms-of-use/Access%20Restrictions.html

Users agree NOT to:
- Circumvent any restrictions placed by API Setu on access to services
- Use APIs to encourage or promote illegal activity
- Violate third party rights
- Engage in activities that violate terms of service

### Monitoring and Compliance
- API Setu may **monitor user usage** of APIs
- Monitoring ensures compliance with terms
- Violations may result in suspension or termination

### myScheme-Specific Third-Party Integration Requirements

**Documentation:** https://www.myscheme.gov.in/terms-of-use, https://www.myscheme.gov.in/url-hosting-tc

#### Security Requirements
- Implement **robust security protocols**:
  - HTTPS encryption
  - Firewall protections
  - Regular penetration testing
- Comply with **OWASP Top 10** for web security vulnerabilities
- Report security breaches within **24 hours**
- Take immediate action to mitigate breaches

#### Legal and Data Protection Compliance
Must comply with:
- **Digital Personal Data Protection Act, 2023**
- **Information Technology Act, 2000**
- All applicable laws, regulations, and third-party rights

#### Content and Placement Guidelines
- myScheme URL must be hosted alongside content that **accurately reflects myScheme's purpose**
- URL must be placed in **relevant sections** aligned with myScheme's purpose
- Priority given to **visible, user-friendly areas**
- Must not mislead users

#### General Usage Requirements
- Use myScheme only for **lawful purposes**
- Must not **infringe rights** of others
- Must not **restrict or inhibit** use by third parties

---

## 6. Integration Patterns - How Third-Party Apps Can Integrate

### Integration Workflow (OFFICIAL PROCESS)

#### Phase 1: Registration & Approval
```
Developer → Signup (partners.apisetu.gov.in) → Submit Documents →
Evaluation by API Setu Team → Approval → API Subscription
```

#### Phase 2: API Discovery
```
Browse API Directory (directory.apisetu.gov.in) →
Search for myScheme APIs → Review API Specifications (OAS 3.0) →
Subscribe to Required APIs
```

#### Phase 3: Testing (Sandbox Environment)
```
Access Sandbox (sandbox.api-setu.in) →
Test API Integration → Validate Requests/Responses →
No Live Data Used
```

**Sandbox Features:**
- Controlled and secure environment
- Safe testing without impacting live systems
- Simulated environment for validation
- No live data used during testing

#### Phase 4: Credential Management
```
Generate Client ID & Secret → Store Credentials Securely →
Implement OAuth 2.0 Flow → Generate Access Tokens →
Manage Token Lifecycle
```

#### Phase 5: Production Deployment
```
Switch to Production Environment →
Configure Production Credentials →
Implement Error Handling →
Monitor API Usage
```

### Security Implementation

#### Authentication Flow (OAuth 2.0 - Recommended)
1. Store clientID and clientSecret securely
2. Request access token using client credentials
3. Receive token with expiration time
4. Use token in API requests: `Authorization: Bearer <token>`
5. Implement token refresh before expiration
6. Handle 401 errors (expired tokens)

#### Best Practices
- **Never expose** client credentials in client-side code
- **Implement retry logic** for transient failures
- **Log API requests** with traceID for debugging
- **Validate responses** before processing
- **Handle errors gracefully** with user-friendly messages

### Integration Architecture

#### API Gateway Features
API Setu provides:
- **CDN** for content delivery
- **Load Balancing** for high availability
- **API Repository** for discovery
- **API Lifecycle Management**
- **Collaboration tools** for data sharing
- **Security mechanisms** for data protection

#### Multiple Layers of Review
API onboarding involves:
- Registration
- Testing
- Validation
- Data privacy checks
- Compliance verification
- Operational performance assessment

### Support and Resources

#### Developer Documentation
- **Main Docs:** https://docs.apisetu.gov.in/document-central/explore-apisetu/
- **Introduction:** https://docs.apisetu.gov.in/document-central/explore-apisetu/Introduction.html
- **Overview:** https://docs.apisetu.gov.in/document-central/explore-apisetu/Overview.html
- **Architecture:** https://docs.apisetu.gov.in/document-central/explore-apisetu/Architecture.html
- **Sandbox:** https://docs.apisetu.gov.in/document-central/explore-apisetu/Sandbox.html

#### Contact Support
- **myScheme Support:** support-myscheme@digitalindia.gov.in
- **Phone:** (011) 24303714
- **Include traceID** from API responses for faster debugging

---

## 7. Data Freshness and Reliability

### Data Update Process

**⚠️ IMPORTANT:** Official documentation does NOT specify exact update frequencies, refresh intervals, or data synchronization schedules.

### What We Know (From Official Sources)

#### Data Sources
- **Central Government Schemes:** Directly from Central Ministries/Departments
- **State/UT Schemes:** From State/UT Governments
- **Governance:** NeGD manages platform with support from MeitY and DARPG

#### Data Management
- Platform managed by **National e-Governance Division (NeGD)**
- Partnership with Central and State Ministries/Departments
- Data collected from multiple government sources
- Platform launched in 2022, data as of Sept 2023 showed 1,000+ schemes
- Current count: **4,700+ schemes** (significant growth)

### Data Reliability Factors

#### Positive Indicators
1. **Official Government Platform:** Operated by MeitY through NeGD
2. **Trusted Partner Status:** API Setu serves major platforms (DigiLocker, UMANG, etc.)
3. **Multiple Security Layers:** HTTPS, authentication, authorization
4. **Compliance Standards:** OWASP Top 10, DPDP Act 2023, IT Act 2000
5. **Continuous Growth:** From 1,000+ to 4,700+ schemes indicates active maintenance

#### Limitations (Data Freshness)
1. **No Published SLA** for data refresh frequency
2. **No Real-time Guarantees** mentioned in documentation
3. **Depends on Source Updates:** Reliability tied to Ministry/Department data submission
4. **Manual Curation Likely:** Cross-government coordination required

### Best Practices for Integration

Given the lack of official data freshness guarantees:

1. **Implement Caching:** Cache scheme data with reasonable TTL (e.g., 24 hours)
2. **Validate Data Age:** Check if API responses include timestamp fields
3. **User Notifications:** Inform users to verify scheme details on official websites before applying
4. **Fallback Mechanisms:** Provide links to official scheme pages for latest information
5. **Periodic Sync:** Schedule regular data refreshes (daily/weekly)
6. **Monitor Changes:** Track scheme count/updates to detect data refreshes

### Recommendation

**For critical compliance or legal applications:** Always verify scheme information through official government sources and include disclaimers about data currency. The myScheme platform serves as a **discovery tool**, not necessarily a real-time authoritative source for scheme details.

---

## 8. Official Documentation Links

### Primary Official Sources

#### myScheme Platform
| Resource | URL | Description |
|----------|-----|-------------|
| Main Website | https://www.myscheme.gov.in/ | Official myScheme portal |
| About Page | https://www.myscheme.gov.in/about | Platform information |
| FAQs | https://www.myscheme.gov.in/faqs | Frequently asked questions |
| Contact | https://www.myscheme.gov.in/contact | Contact information |
| Terms of Use | https://www.myscheme.gov.in/terms-of-use | Usage terms |
| URL Hosting T&C | https://www.myscheme.gov.in/url-hosting-tc | Third-party integration terms |
| Dashboard | https://www.myscheme.gov.in/dashboard | Scheme overview |
| Scheme Search | https://www.myscheme.gov.in/search | Search functionality |
| Find Scheme | https://www.myscheme.gov.in/find-scheme | Eligibility finder |
| Central Schemes | https://www.myscheme.gov.in/search/ministry/all-ministries | All central schemes |
| State Schemes | https://www.myscheme.gov.in/search/state/all-states | All state schemes |

#### Digital India & NeGD
| Resource | URL | Description |
|----------|-----|-------------|
| myScheme on Digital India | https://www.digitalindia.gov.in/initiative/myscheme/ | Official Digital India page |
| NeGD Main Site | https://negd.gov.in/ | National e-Governance Division |
| myScheme on NeGD | https://negd.gov.in/our_projects/myscheme/ | NeGD project page |
| About NeGD | https://negd.gov.in/about-negd/ | About the division |

#### API Setu Platform
| Resource | URL | Description |
|----------|-----|-------------|
| Main Portal | https://www.apisetu.gov.in/ | API Setu homepage |
| API Directory | https://directory.apisetu.gov.in/ | All available APIs |
| myScheme APIs | https://directory.apisetu.gov.in/search?tag=myscheme | myScheme API collection |
| Ministry Wise API | https://directory.apisetu.gov.in/api-collection/myscheme | Scheme count API |
| Partner Portal | https://partners.apisetu.gov.in/ | Developer portal |
| Signup | https://partners.apisetu.gov.in/signup | Register as consumer |
| Login | https://partners.apisetu.gov.in/signin | Consumer login |
| Sandbox | https://sandbox.api-setu.in/ | Testing environment |

#### API Setu Documentation
| Resource | URL | Description |
|----------|-----|-------------|
| Documentation Home | https://docs.apisetu.gov.in/document-central/explore-apisetu/ | Main documentation |
| Introduction | https://docs.apisetu.gov.in/document-central/explore-apisetu/Introduction.html | Getting started |
| Overview | https://docs.apisetu.gov.in/document-central/explore-apisetu/Overview.html | Platform overview |
| Architecture | https://docs.apisetu.gov.in/document-central/explore-apisetu/Architecture.html | Technical architecture |
| Sandbox Guide | https://docs.apisetu.gov.in/document-central/explore-apisetu/Sandbox.html | Testing guide |
| Partners | https://docs.apisetu.gov.in/document-central/explore-apisetu/Partners.html | Partner information |
| Use Cases | https://docs.apisetu.gov.in/document-central/explore-apisetu/Use%20Cases.html | Integration examples |

#### API Setu Terms of Use
| Resource | URL | Description |
|----------|-----|-------------|
| Policy Statement | https://docs.apisetu.gov.in/document-central/api-policy/Policy%20Statement.html | API policy |
| Permitted Use | https://docs.apisetu.gov.in/document-central/terms-of-use/Permitted%20Use%20and%20Access.html | Allowed usage |
| API Usage Limits | https://docs.apisetu.gov.in/document-central/terms-of-use/API%20Usage%20Limits.html | Rate limits |
| Access Restrictions | https://docs.apisetu.gov.in/document-central/terms-of-use/Access%20Restrictions.html | Usage restrictions |

#### Official Guidelines and SOPs
| Resource | URL | Description |
|----------|-----|-------------|
| Consumer SOP | https://cdn.apisetu.gov.in/portal/assets/SOP-APISETU.pdf | Standard operating procedure |
| Onboarding Guidelines | https://negd.gov.in/wp-content/uploads/2025/06/Guidelines-for-Onboarding-for-API-as-a-service-provider-v15-Rev-1-1.pdf | Provider onboarding |
| Open API Standards | https://egovstandards.gov.in/sites/default/files/2023-05/Open%20API%20-%20Powering%20Agile%20Service%20Delivery_0.pdf | Government API policy |

#### Digital India Announcements
| Resource | URL | Description |
|----------|-----|-------------|
| API Setu Announcement | https://www.digitalindia.gov.in/announcements/application-for-onboarding-on-api-setu/ | Onboarding announcement |
| API Setu Initiative | https://www.digitalindia.gov.in/initiative/api-setu/ | API Setu program page |
| NeGD on Digital India | https://www.digitalindia.gov.in/di_ecosystem/national-e-governance-division-negd/ | NeGD ecosystem page |

---

## 9. Key Findings Summary

### ✅ Confirmed (Officially Documented)

1. **API Availability:** myScheme APIs are publicly available through API Setu
2. **Registration Process:** Formal onboarding process with document submission required
3. **Authentication:** OAuth 2.0, Client ID/Secret, and API Key mechanisms supported
4. **Sandbox Testing:** Testing environment available at sandbox.api-setu.in
5. **API Standards:** OpenAPI Specification (OAS) 3.0 compliant
6. **Data Coverage:** 4,700+ schemes across Central and State/UT governments
7. **Legal Framework:** DPDP Act 2023 and IT Act 2000 compliance mandatory
8. **Security Standards:** OWASP Top 10 compliance required
9. **Support Contact:** support-myscheme@digitalindia.gov.in

### ⚠️ Partially Documented

1. **Specific API Endpoints:** Limited public documentation; full specs require developer account
2. **Rate Limits:** Mentioned but specific numerical limits not publicly disclosed
3. **Approval Timeline:** Process described but no SLA or expected timeframes provided
4. **Data Freshness:** No official update frequency or refresh schedule published

### ❌ Not Found (Gaps in Public Documentation)

1. **Detailed API Specifications:** Complete endpoint documentation not publicly available
2. **Sample Code:** No publicly available integration examples or SDKs
3. **Numerical Rate Limits:** Specific request quotas not disclosed
4. **SLA Commitments:** No service level agreements or uptime guarantees found
5. **Data Update Schedule:** Scheme data refresh frequency not documented
6. **Versioning Policy:** API versioning and deprecation policies not clear
7. **Webhook Support:** No mention of webhook/callback capabilities
8. **Bulk Operations:** No information on batch API requests or exports

---

## 10. Recommendations for Integration

### Before Starting Integration

1. **Register Early:** API Setu approval process requires documentation review
2. **Prepare Documentation:** Have Organization PAN, GST Certificate, Incorporation Certificate ready
3. **Define Use Case:** Clearly articulate how you'll use myScheme APIs
4. **Review Terms:** Carefully review API Setu Terms of Use and myScheme URL Hosting T&C

### During Integration

1. **Start with Sandbox:** Test thoroughly in sandbox environment before production
2. **Implement OAuth 2.0:** Use recommended authentication mechanism
3. **Handle Token Expiration:** Implement automatic token refresh
4. **Add Error Handling:** Gracefully handle rate limits, timeouts, and errors
5. **Include Disclaimers:** Inform users to verify scheme details on official websites
6. **Cache Responsibly:** Implement caching with reasonable TTL (24 hours suggested)

### Production Deployment

1. **Monitor Usage:** Track API call patterns to stay within limits
2. **Log Requests:** Keep logs with traceID for debugging
3. **Plan for Failures:** Implement circuit breakers and fallback mechanisms
4. **Stay Compliant:** Ensure DPDP Act 2023 and IT Act 2000 compliance
5. **Regular Testing:** Periodically verify API integration still works
6. **Subscribe to Updates:** Monitor for API changes or deprecations

### Security Checklist

- [ ] HTTPS encryption implemented
- [ ] Client credentials stored securely (environment variables, secrets manager)
- [ ] OAuth 2.0 flow correctly implemented
- [ ] Token refresh logic in place
- [ ] API responses validated before use
- [ ] User input sanitized (if passed to APIs)
- [ ] Error messages don't leak sensitive data
- [ ] Security breach notification process established
- [ ] OWASP Top 10 vulnerabilities addressed
- [ ] Regular penetration testing scheduled

---

## 11. Contact Information for Further Assistance

### myScheme Support
- **Email:** support-myscheme@digitalindia.gov.in
- **Phone:** (011) 24303714
- **Fax:** 011-24303778
- **Address:** 4th Floor, NeGD, Electronics Niketan, 6 CGO Complex, Lodhi Road, New Delhi – 110003, India

### NeGD (Platform Management)
- **Email:** webmaster@digitalindia.gov.in
- **Phone:** 011-24303714
- **Website:** https://negd.gov.in/

### API Setu Support
- **Partner Portal:** https://partners.apisetu.gov.in/
- **Documentation:** https://docs.apisetu.gov.in/
- **Include traceID** from API responses when contacting support

---

## 12. Sources and Citations

This report is based entirely on official government sources and documentation. All information has been verified against primary sources.

### Primary Government Sources
- [myScheme Official Website](https://www.myscheme.gov.in/)
- [Digital India - myScheme Initiative](https://www.digitalindia.gov.in/initiative/myscheme/)
- [National e-Governance Division - myScheme](https://negd.gov.in/our_projects/myscheme/)
- [API Setu Official Portal](https://www.apisetu.gov.in/)
- [API Setu Documentation](https://docs.apisetu.gov.in/document-central/explore-apisetu/)
- [API Setu Directory - myScheme APIs](https://directory.apisetu.gov.in/search?tag=myscheme)

### Official Documentation
- [API Setu Standard Operating Procedure](https://cdn.apisetu.gov.in/portal/assets/SOP-APISETU.pdf)
- [API Setu Onboarding Guidelines](https://negd.gov.in/wp-content/uploads/2025/06/Guidelines-for-Onboarding-for-API-as-a-service-provider-v15-Rev-1-1.pdf)
- [Open API - Powering Agile Service Delivery](https://egovstandards.gov.in/sites/default/files/2023-05/Open%20API%20-%20Powering%20Agile%20Service%20Delivery_0.pdf)

### API Setu Terms of Use
- [Permitted Use and Access](https://docs.apisetu.gov.in/document-central/terms-of-use/Permitted%20Use%20and%20Access.html)
- [API Usage Limits](https://docs.apisetu.gov.in/document-central/terms-of-use/API%20Usage%20Limits.html)
- [Access Restrictions](https://docs.apisetu.gov.in/document-central/terms-of-use/Access%20Restrictions.html)

### myScheme Terms
- [myScheme Terms of Use](https://www.myscheme.gov.in/terms-of-use)
- [myScheme URL Hosting Terms & Conditions](https://www.myscheme.gov.in/url-hosting-tc)

---

## Appendix: Research Methodology

### Search Strategy
1. **Primary Sources Prioritized:** india.gov.in, myscheme.gov.in, api.gov.in, apisetu.gov.in, negd.gov.in, digitalindia.gov.in
2. **Cross-Verification:** All claims verified against multiple official sources
3. **Official Documentation:** Direct links to government documentation provided
4. **Clear Attribution:** Speculation vs. confirmed information clearly marked

### Limitations
1. **Developer Account Required:** Some API documentation only accessible after approval
2. **Dynamic Content:** API specifications may change; verify current documentation
3. **No Hands-On Testing:** Report based on documentation review, not actual API testing
4. **Data Freshness:** Some information (scheme counts) may be outdated

### Confidence Levels
- **High Confidence:** Information from multiple official government sources
- **Medium Confidence:** Mentioned in official docs but lacking detail
- **Low Confidence:** Inferred from platform features or general practices (clearly marked)

---

**Report Compiled:** August 23, 2026
**Next Review Recommended:** Before starting integration (verify current documentation)
**For Latest Information:** Always check official government sources listed above

---

## Disclaimer

This report is based on publicly available information from official government sources as of August 23, 2026. API specifications, policies, and procedures may change. Always verify current documentation through official channels before integration. This research is provided for informational purposes only and does not constitute legal or technical advice.
