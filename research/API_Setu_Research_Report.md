# API Setu Research Report
**Comprehensive Analysis of India's API Setu Platform**

*Research Date: August 23, 2026*

---

## Executive Summary

API Setu (apisetu.gov.in) is India's national Open API Platform operated by the Ministry of Electronics and Information Technology (MeitY) under the National e-Governance Division (NeGD). Launched in March 2020, it serves as a consolidated, secure gateway for information and service exchange between government departments, private organizations, startups, and developers.

**Current Scale (March 2026):**
- **8,036 APIs** hosted on the platform
- **6,592 consumers** registered
- **2,559 publishers** contributing APIs
- **10,530 organizations** onboarded
- **~80 million transactions** processed monthly

---

## 1. What is API Setu

### Official Purpose

API Setu is an Open API (Application Programming Interface) Platform designed to:

- Enable **swift, transparent, safe, and reliable information sharing** across applications
- Build an **open and interoperable digital platform** for seamless service delivery across government silos
- Promote **innovation** through standardized API access
- Manage the **full API lifecycle** from publishing to consumption
- Support both **public and private ecosystems**

### Role in India's Digital Infrastructure

API Setu serves as the **API aggregator for Government of India**, acting as a critical component of India's Digital Public Infrastructure (DPI). It powers major national platforms including:

- **DigiLocker** - Digital document storage and sharing
- **MeriPehchaan** - National Single Sign-On (SSO)
- **National Academic Depository (NAD)** - Educational document verification
- **myScheme** - Government schemes discovery
- **UMANG** - Unified Mobile Application for New-age Governance
- **CBSE** - Educational services
- **GSTN** - Goods and Services Tax Network

### Policy Framework

The platform was established following the **Open API Policy** notified by MeitY in July 2015, which aimed to develop an open and interoperable platform to enable seamless service delivery across government.

---

## 2. Available API Categories

### Major Categories

API Setu organizes APIs across **18+ categories**:

1. **Banking, Financial Services and Insurance (BFSI)**
2. **Identity & Documents**
3. **Education & Learning**
4. **Health & Wellness**
5. **Transport & Infrastructure**
6. **Agriculture, Rural & Environment**
7. **Social Welfare & Empowerment**
8. **Business & Entrepreneurship**
9. **Skills & Employment**
10. **Government & Public Sector**
11. **Public Safety, Law & Justice**
12. **Sports & Culture**
13. **Defence & Armed Forces**
14. **Travel & Tourism**
15. **Housing & Shelter**
16. **Science, IT & Communications**
17. **Utility**
18. **Others**

### API Types

APIs are classified into three main types:

#### Document APIs
Handle **user-specific data** requiring consent:
- PAN (Permanent Account Number)
- Academic certificates
- Income records
- DigiLocker documents
- Aadhaar-linked documents

#### Service APIs
Provide **non-user-specific data**:
- Organization PAN verification
- GSTN (GST Number) verification
- myScheme - Government schemes information
- LokOS - Operating system services
- Vehicle registration (VAHAN)
- Driving license (Sarathi)
- PMJAY (Ayushman Bharat)
- PM-KISAN records

#### Listing APIs
Enable API partners to **list their APIs** for discovery:
- CoWIN (COVID-19 vaccination)
- Various departmental services

### Key Verification APIs

The platform hosts **over 200 KYC APIs** including:
- **Aadhaar verification**
- **PAN card verification**
- **Bank account verification**
- **GSTN verification**
- **Importer Exporter Code (IEC) verification**
- **DigiLocker document verification**

---

## 3. Consumer Registration Process

### Step 1: Access the Partners Portal

**URL:** https://partners.apisetu.gov.in/signup

### Step 2: Sign Up Options

Two authentication methods available:

#### Option A: DigiLocker-MeriPehchaan SSO
- Use existing MeriPehchaan credentials
- Simplified authentication process
- Recommended for government entities

#### Option B: Traditional Username/Password
- Standard registration flow
- Email verification required

### Step 3: Submit Registration Documents

Required documents for organizations:

1. **Proof of Identity** - Authorized representative
2. **Authority Letter** - Authorization to access APIs
3. **Organization PAN** - Tax identification
4. **GST Registration Certificate** - For business entities
5. **Certificate of Incorporation** - Company registration proof
6. **Valid Use Case** - Detailed description of API usage intent

**Important Notes:**
- Use **domain-registered email IDs** only
- **One request per organization** will be entertained
- Requests must come from authorized representatives

### Step 4: Evaluation and Approval

Process flow:
1. **API Setu Management Team** evaluates the request
2. **Use case validation** against platform policies
3. **API provider approval** required for specific APIs
4. **Approval granted** with credentials and documentation

### Step 5: Post-Approval Access

Once approved, consumers can:
- **Subscribe to APIs** from the directory
- **Generate API keys** for authentication
- **Access sandbox environment** for testing
- **Deploy APIs** in production applications
- **Monitor usage** through dashboards

---

## 4. myScheme Integration

### Availability through API Setu

**YES**, myScheme APIs are **available through API Setu**.

### About myScheme

- **Launch Date:** July 4, 2022 (by Prime Minister)
- **Purpose:** One-stop discovery platform for government schemes
- **Coverage:** Over 4,700 Central Government and State/UT Government schemes
- **Integration:** Powered by API Setu infrastructure

### Available myScheme APIs

The API directory includes:

**Ministry Wise Schemes Count API (OAS 3.0)**
- **Endpoint:** Available at directory.apisetu.gov.in/api-collection/myscheme
- **Function:** Retrieve scheme counts by ministry
- **Use Case:** Scheme discovery and aggregation

### How myScheme Works

**Three-step discovery process:**

1. **User Input:** Citizens enter demographic and income information
2. **Matching:** myScheme displays relevant eligible schemes
3. **Application:** Users navigate to respective scheme application URLs

### Integration Benefits

- **Eligibility-based discovery:** Technology-driven scheme matching
- **Seamless access:** Integration with MeriPehchaan SSO
- **Comprehensive coverage:** Central and State schemes in one place
- **API-driven:** Enables third-party applications to integrate scheme discovery

---

## 5. DigiLocker Integration

### Availability through API Setu

**YES**, DigiLocker APIs are **extensively available through API Setu**.

### DigiLocker Integration Types

API Setu offers **two integration models** for DigiLocker:

#### 1. Issuer APIs

**Purpose:** Organizations issuing documents & certificates

**Key Features:**
- **Push Model:** Directly issue digital documents to citizen DigiLockers
- **Pull Model:** Enable users to search and fetch documents from issuer repositories
- **Requirements:** Become a registered issuer with DigiLocker
- **API Specification:** DigiLocker Issuer API Specification v1.13 (May 2024)

**Pull URI Request API:**
- REST-based API implemented by issuer organizations
- Allows locker owners to query issuer repository
- Query by Aadhaar number or other identifiers
- For documents not Aadhaar-seeded

#### 2. Requester/Partner APIs

**Purpose:** Organizations needing verified digital documents

**Key Features:**
- **Document Verification:** Access user documents with consent
- **KYC Operations:** Integrate document verification in workflows
- **Consent-based Access:** User authorization required
- **API Specification:** Authorized Partner API Specification v2.2 (October 2022)

### DigiLocker API Workflow

**For Requesters/Consumers:**

1. **Create DigiLocker Request**
   - Initialize document fetch request
   - Specify required document types

2. **Obtain User Consent**
   - User authenticates with DigiLocker
   - User approves document sharing
   - OTP verification if required

3. **Fetch Documents**
   - Retrieve consented documents instantly
   - Receive verified, digitally signed documents
   - Documents maintain legal validity

### Available Document Types

DigiLocker enables access to **200+ document types** including:

- **Identity Documents:** Aadhaar, PAN, Driving License
- **Educational Certificates:** Degrees, marksheets, diplomas
- **Vehicle Documents:** Registration certificates, insurance
- **Professional Licenses:** Medical, legal, engineering licenses
- **Government Issued:** Birth certificates, income certificates
- **Property Documents:** Land records, property tax receipts

### Use Cases

- **Paperless KYC:** Financial services onboarding
- **Admission Processes:** Educational institutions
- **Employment Verification:** Background checks
- **Loan Applications:** Income and identity verification
- **Government Services:** Subsidy and benefit applications

### Integration Resources

**Official Documentation:**
- API Setu DigiLocker Page: https://apisetu.gov.in/digilocker
- Issuer API Specification: https://cf-media.api-setu.in/resources/DigiLocker-Issuer-APISpecification-v1-13.pdf
- Partner API Specification: https://cf-media.api-setu.in/resources/DigitalLocker-AuthorizedPartnerAPI-Specificationv2.2.pdf

---

## 6. Authorization Model

### Authentication Methods

#### 1. OAuth 2.0

**Implementation:**
- Industry-standard authorization framework
- Token-based authentication
- Supports multiple product configurations

**OAuth Workflow:**
1. Generate OAuth keys in Partners Portal
2. Select environment (Sandbox/Production)
3. Obtain clientID and secret
4. Request access token
5. Use Bearer token in API requests

**Authorization Header Format:**
```
Authorization: Bearer <token-value>
```

**Key Features:**
- **Flexible Configuration:** Single key set for multiple APIs or separate keys per API
- **Environment-specific:** Sandbox keys only access sandbox; production keys only access production
- **Token Lifecycle Management:** Tokens can be regenerated; old credentials invalidate immediately

#### 2. API Keys

**Standard API Key Authentication:**
- Generated through Partners Portal (partners.apisetu.gov.in)
- Unique keys per consumer organization
- Environment-specific (Sandbox vs Production)
- Can be regenerated when needed

**Key Management:**
- **Generation:** Admin-only access to create keys
- **Regeneration:** Instant invalidation of old keys
- **Rotation:** Independent process, no "Save changes" required
- **Scope:** Can be configured per API or across multiple APIs

#### 3. MeriPehchaan SSO Integration

**National Single Sign-On:**
- Unified authentication across government services
- Integration with API Setu Partners Portal
- Simplifies user authentication for consumers

**Configuration Process:**
1. Register application on MeriPehchaan Developer Portal
2. Obtain Client ID and Client Secret
3. Configure in API Setu Partners Portal
4. Enable as External Identity Provider
5. Test integration before go-live

### Sandbox vs Production Access

#### Sandbox Environment

**URL:** https://sandbox.api-setu.in

**Key Features:**
- **No Sign-up Required:** Immediate testing access
- **Simulated Data:** No live/real data used
- **Full Functionality:** Near-production feature parity
- **Risk-Free Testing:** No impact on production systems
- **API Validation:** Test requests and responses
- **Development Environment:** Available for UAT and development

**Purpose:**
- Application testing and validation
- API workflow optimization
- Compatibility issue identification
- Integration debugging
- Developer training

**Limitations:**
- Separate credentials from production
- Sandbox keys cannot access production APIs
- May have reduced rate limits
- Simulated responses, not real government data

#### Production Environment

**Access Process:**
1. **Complete registration** with all required documents
2. **Use case approval** by API Setu team
3. **API provider approval** for specific APIs (principal departments)
4. **KYC verification** and compliance checks
5. **Production credentials issued** after approval
6. **Go-live authorization** granted

**Requirements:**
- Valid business registration
- Approved use case
- Compliance with terms of use
- Security and privacy standards adherence
- API provider consent (for specific APIs)

**Features:**
- Access to **real government data**
- **Production-grade SLA** guarantees
- **Higher rate limits** than sandbox
- **Official integration** status
- **Support and monitoring** included

### Security Measures

- **Consent Management:** User authorization required for personal data
- **Encryption Standards:** Secure data transmission (HTTPS/TLS)
- **Access Logging:** Audit trails for compliance
- **Rate Limiting:** Protection against abuse
- **IP Whitelisting:** Optional additional security
- **Data Anonymization:** Privacy protection for sensitive data

---

## 7. Terms and Allowed Usage

### Commercial Use

#### Permitted Commercial Activities

**YES**, commercial use is **explicitly permitted** with conditions:

1. **API Access Rights:**
   - Each user permits and licenses other users to use published APIs
   - Includes using APIs for developing codes, software, systems, portals, or platforms

2. **Commercial Licensing:**
   - Independently developed solutions can be **sold**
   - Solutions can be **leased** to third parties
   - Solutions can be **sublicensed** commercially

3. **Use Case Requirements:**
   - Must use valid credentials
   - Only for **internal and approved use cases**
   - Must comply with **documented usage parameters**

### Usage Restrictions

#### Prohibited Activities

1. **Unauthorized Access:**
   - Access beyond authorized parameters strictly prohibited
   - No exploitation of system vulnerabilities
   - No unauthorized credential sharing

2. **Data Usage:**
   - User data cannot be used beyond approved purposes
   - No reselling of raw government data without permission
   - Consent required for personal data usage

3. **System Abuse:**
   - No activities that could overload the platform
   - No reverse engineering of APIs
   - No automated scraping beyond API limits

### Rate Limits

#### API Usage Limits

**Platform-level Controls:**
- Number and **frequency of API calls** regulated
- Usage **quotas assigned** per consumer
- Must comply with assigned limits

**Consequences of Exceeding Limits:**
- **Access restrictions** may be imposed
- **Temporary suspension** for policy breaches
- **Permanent revocation** for serious violations

**Rate Limit Factors:**
- API type and category
- Consumer subscription tier
- Approved use case scope
- Historical usage patterns

### Access Restrictions

#### Grounds for Suspension

1. **Breach of usage policies**
2. **Exceeding rate limits**
3. **Unauthorized data usage**
4. **Security violations**
5. **Non-compliance with consent requirements**

### Permitted Use and Access

#### Lawful Usage Requirements

**Compliance Mandates:**
1. **Lawful and Authorized Purposes Only:**
   - Access must align with approved use cases
   - Must comply with API Setu documentation

2. **Valid Credentials:**
   - Use only issued credentials
   - No credential sharing or unauthorized access

3. **Approved Use Cases:**
   - Stick to internal and approved applications
   - Any deviation strictly prohibited

4. **Documentation Compliance:**
   - Follow technical specifications
   - Adhere to integration guidelines
   - Respect data usage policies

### Permissions and Approvals

#### API Provider Requirements

**Issuers/Publishers Must:**
- Possess all necessary **permissions and approvals**
- Obtain **authorizations** to host APIs
- Have rights to **share data** through platform
- Maintain approvals **at all times**
- Comply with **third-party approval requirements**

### Governance

**Platform Operator:**
- **National e-Governance Division (NeGD)**
- Under Ministry of Electronics and Information Technology (MeitY)
- Government of India

**Policy Framework:**
- Open API Policy (July 2015)
- API Setu Terms of Use
- Individual API-specific terms
- Data protection regulations

---

## 8. Other Relevant Government Service APIs

### Major Government Service APIs Available

#### 1. Identity and Verification Services

**Aadhaar Services:**
- Aadhaar verification API
- eKYC services
- Demographic authentication
- Biometric authentication (where authorized)

**PAN Services:**
- PAN verification API
- Track PAN application status
- PAN-Aadhaar linking verification

**Voter ID:**
- Electoral roll verification
- Voter ID authentication

#### 2. Financial Services

**GSTN (Goods and Services Tax):**
- GST number verification
- GST return status
- Tax compliance verification

**Banking:**
- Bank account verification
- IFSC code validation
- Penny drop verification
- Account statement verification (with consent)

**Financial Inclusion:**
- PM-KISAN beneficiary verification
- Direct Benefit Transfer (DBT) status
- PMJAY (Ayushman Bharat) eligibility

#### 3. Transport and Infrastructure

**VAHAN (Vehicle Registration):**
- Vehicle registration details
- RC verification
- Vehicle ownership transfer status

**Sarathi (Driving License):**
- Driving license verification
- License validity check
- Endorsement details

**FASTag:**
- FASTag account verification
- Toll transaction history

#### 4. Education Services

**National Academic Depository (NAD):**
- Academic certificate verification
- Degree authenticity check
- Marksheet validation

**CBSE:**
- Board exam results
- Certificate verification
- School registration details

**UGC:**
- University recognition status
- Degree verification

#### 5. Healthcare

**Ayushman Bharat (PMJAY):**
- Beneficiary verification
- Eligibility check
- Empaneled hospital search

**CoWIN:**
- Vaccination certificate
- Vaccination status
- Appointment scheduling (during campaigns)

#### 6. Property and Land

**Land Records:**
- Property ownership verification
- Land records digitization
- Mutation status

**Property Tax:**
- Tax payment verification
- Property assessment details

#### 7. Employment and Skills

**EPF (Employees' Provident Fund):**
- UAN verification
- EPF balance inquiry
- Claim status

**ESI (Employee State Insurance):**
- ESI number verification
- Contribution status

**Skill India:**
- Certification verification
- Training program details

#### 8. Business Services

**MCA (Ministry of Corporate Affairs):**
- Company registration verification
- Director details
- Company compliance status

**Udyam Registration:**
- MSME registration verification
- Udyam certificate details

**Import/Export:**
- IEC (Import Export Code) verification
- Customs documentation

#### 9. Social Welfare

**Pension Schemes:**
- Beneficiary verification
- Pension payment status
- Scheme eligibility

**Scholarship Programs:**
- Scholarship application status
- Beneficiary verification

#### 10. Utility Services

**Electricity:**
- Consumer number verification
- Bill payment status
- Connection details

**Water:**
- Consumer connection verification
- Bill payment records

**Gas:**
- LPG connection verification
- Subsidy status (PAHAL)

### Cross-Platform Integration

**UMANG (Unified Mobile Application):**
- Consolidated access to 1,400+ government services
- Integration with API Setu backend
- Pan-India service delivery

**India Stack Components:**
- Aadhaar authentication
- DigiLocker document access
- UPI payment integration
- Account Aggregator framework

### API Discovery

**API Directory:** https://directory.apisetu.gov.in
- Browse all available APIs
- Search by category, department, or service
- View API specifications
- Check integration requirements

---

## 9. Integration Requirements and Process

### Technical Requirements

#### 1. API Standards Compliance

**OpenAPI Specification 3.0:**
- All APIs must adhere to **OAS 3.0** standard
- API definitions in **YAML or JSON** format
- REST-based architecture required
- Standard HTTP methods (GET, POST, PUT, DELETE)

**Required Documentation:**
- API endpoint specifications
- Request/response schemas
- Authentication requirements
- Error code definitions
- Rate limit specifications

#### 2. Environment Setup

**Development Environments:**
- **Development:** Initial coding and unit testing
- **UAT (User Acceptance Testing):** Integration testing
- **Sandbox/Pre-Production:** Near-production simulation
- **Production:** Live environment

**Infrastructure Requirements:**
- **Multiple environment support** mandatory
- **Separate configurations** per environment
- **Near-production functionality** in sandbox
- **User simulation capabilities**

#### 3. Security and Compliance

**Mandatory Security Controls:**
- **HTTPS/TLS encryption** for all API calls
- **OAuth 2.0 or API key** authentication
- **Consent management** for personal data
- **Data encryption** at rest and in transit
- **Access logging** for audit trails
- **IP whitelisting** (optional, recommended)

**Privacy Compliance:**
- User consent required for personal data
- Data retention policies adherence
- Right to erasure support
- Data portability compliance
- Transparent data usage disclosure

#### 4. Performance Standards

**Service Level Requirements:**
- **Resolution time:** 4 hours for critical issues
- **Uptime SLA:** High availability required
- **Response time:** As per API specifications
- **Error handling:** Comprehensive error codes
- **Failover mechanisms:** Redundancy required

### Integration Process

#### For API Consumers

**Step 1: Registration (Week 1)**
1. Access partners.apisetu.gov.in/signup
2. Complete registration form
3. Submit required documents:
   - Organization PAN
   - GST certificate
   - Incorporation certificate
   - Authority letter
   - Proof of identity
4. Define use case in detail

**Step 2: Approval Process (1-2 Weeks)**
1. API Setu team evaluates application
2. Use case validation
3. Document verification
4. API provider approval (if required)
5. Approval notification sent

**Step 3: Sandbox Access (Immediate Post-Approval)**
1. Receive sandbox credentials
2. Access API documentation
3. Explore API directory
4. Subscribe to required APIs
5. Generate sandbox API keys

**Step 4: Development and Testing (Variable Duration)**
1. Set up development environment
2. Implement API integration
3. Test in sandbox environment
4. Validate request/response handling
5. Test error scenarios
6. Optimize API calls
7. Implement retry mechanisms
8. Add logging and monitoring

**Step 5: Production Approval (1-2 Weeks)**
1. Submit production access request
2. Demonstrate successful sandbox testing
3. Security review (if required)
4. API provider final approval
5. Production credentials issued

**Step 6: Go-Live (Post Production Approval)**
1. Configure production environment
2. Update API endpoints to production
3. Implement production API keys
4. Set up monitoring dashboards
5. Deploy to production
6. Monitor initial transactions
7. Performance optimization

**Step 7: Ongoing Monitoring**
1. Track API usage metrics
2. Monitor error rates
3. Review performance dashboards
4. Compliance reporting
5. Regular security audits

#### For API Publishers

**Step 1: Onboarding Application**
1. Download application form: negd.gov.in
2. Complete detailed questionnaire
3. Define API specifications
4. Document use cases
5. Submit for evaluation

**Step 2: Technical Evaluation**
1. API testing on technical criteria
2. Security assessment
3. Performance benchmarking
4. Documentation review
5. Detailed report generation

**Step 3: Infrastructure Setup**
1. Create Development environment
2. Set up UAT environment
3. Configure Sandbox/Pre-Production
4. Production environment preparation
5. Implement monitoring dashboards

**Step 4: Integration with NeGD Systems**
1. Connect to reporting dashboards
2. Enable automated KPI data fetching
3. Set up error-free reporting
4. Configure performance score measurement
5. Enable rolling basis monitoring

**Step 5: API Publishing**
1. Upload API file (OAS 3.0 YAML format)
2. Complete metadata
3. Define access policies
4. Set rate limits
5. Submit for review

**Step 6: Review and Approval**
1. API Setu team technical review
2. Security validation
3. Documentation completeness check
4. Use case alignment verification
5. Publication approval

**Step 7: Go-Live**
1. API listed in directory
2. Available for consumer discovery
3. Monitoring and analytics enabled
4. Support channel activation

### Support and Resources

**Official Documentation:**
- **API Setu Docs:** https://docs.apisetu.gov.in
- **Integration Guides:** Available per API
- **FAQs:** https://apisetu.gov.in/faq
- **Standard Operating Procedure:** https://cdn.apisetu.gov.in/portal/assets/sop-apisetu-v1.pdf

**Developer Support:**
- **Email:** Contact through partners portal
- **Documentation Portal:** Comprehensive guides
- **API Directory:** Browse and explore APIs
- **Sandbox:** No-signup testing environment

**Technical Specifications:**
- **OpenAPI 3.0 Standard:** https://spec.openapis.org/oas/v3.0.3.html
- **REST API Guidelines:** Available in docs
- **Security Best Practices:** Platform-specific guides

### Integration Timeline Estimate

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Registration | 1 week | Document submission, approval waiting |
| Approval | 1-2 weeks | Evaluation, API provider consent |
| Development | 2-8 weeks | Integration coding, sandbox testing |
| Production Approval | 1-2 weeks | Security review, final approvals |
| Deployment | 1 week | Go-live, monitoring setup |
| **Total** | **6-14 weeks** | End-to-end integration |

*Note: Timeline varies based on use case complexity, API type, and approval requirements*

---

## 10. Cost and Pricing

### Platform Access Cost

#### API Setu Platform

**FREE for Sandbox Access:**
- **No registration fee** for sandbox environment
- **Immediate access** without sign-up
- **Full testing capabilities** available at no cost
- **No usage charges** in sandbox

**FREE for Registered Consumers:**
- **No platform fees** for approved API consumers
- **No subscription charges** to API Setu
- **No listing fees** for accessing API directory

### API-Specific Pricing

#### Government APIs

**Generally FREE for approved use cases:**
- Most government service APIs are **free** for:
  - Government departments
  - Public service applications
  - Approved social welfare projects
  - Educational institutions

**Volume-Based or Transactional Pricing:**
- Some APIs may have usage-based charges
- Pricing varies by API provider (principal department)
- Negotiated on enterprise/high-volume basis

#### Commercial Third-Party APIs

**Modular Pricing (Enterprise Negotiation):**

While API Setu itself doesn't charge, third-party API providers (like Setu.co, a commercial entity separate from API Setu) may have their own pricing:

**Example Pricing Models (Third-Party APIs):**

1. **Account Aggregator APIs:**
   - ₹10 to ₹25 per successful data fetch
   - Flat API fee per consent execution

2. **BBPS (Bill Payments):**
   - Transaction fee model
   - Small commission per successful payment
   - Varies by biller category

3. **WhatsApp & UPI Links:**
   - Flat fee per transaction
   - Small percentage of transaction volume
   - Similar to standard payment gateways

4. **KYC Verification:**
   - Per verification charge
   - Volume discounts available
   - Enterprise pricing on negotiation

**Important Distinction:**
- **API Setu (Government Platform):** FREE access
- **Individual API Providers:** May charge based on their policies
- **Commercial Service Providers:** Separate pricing structures

### Cost Structure Summary

| Component | Cost | Notes |
|-----------|------|-------|
| **API Setu Registration** | FREE | No platform fees |
| **Sandbox Access** | FREE | Unlimited testing |
| **Government Service APIs** | Generally FREE | For approved use cases |
| **High-Volume Commercial Use** | VARIABLE | Negotiated with API provider |
| **Third-Party Commercial APIs** | VARIABLE | Provider-specific pricing |
| **Technical Support** | FREE | Through official channels |
| **Documentation Access** | FREE | Complete documentation |

### Pricing Transparency

**Important Notes:**

1. **No Hidden Costs:**
   - API Setu platform charges **no fees**
   - Individual API providers set their own terms

2. **Use Case Dependent:**
   - Government-to-Government (G2G): Usually FREE
   - Government-to-Citizen (G2C): Usually FREE
   - Business-to-Consumer (B2C): May have costs
   - High-volume commercial: Negotiated pricing

3. **Enterprise Negotiation:**
   - Volume-based discounts available
   - Custom pricing for large deployments
   - SLA-based pricing tiers possible

4. **Free Tier Availability:**
   - Many APIs offer free tier for testing
   - Limited transactions in free tier
   - Upgrade required for production scale

### Recommendations for Cost Planning

1. **Review Individual API Terms:**
   - Check each API's specific pricing in directory
   - Contact API provider for commercial terms

2. **Start with Sandbox:**
   - Test completely in free sandbox
   - Validate integration before production

3. **Negotiate in Advance:**
   - For high-volume use cases
   - For enterprise deployments
   - For long-term contracts

4. **Monitor Usage:**
   - Track API call volumes
   - Optimize to reduce costs
   - Use caching where appropriate

---

## Key Takeaways

### Strengths of API Setu

1. **Comprehensive Coverage:** 8,036+ APIs across all government services
2. **Massive Scale:** 80 million monthly transactions
3. **Free Access:** No platform fees, free sandbox
4. **Standardization:** OpenAPI 3.0 compliance
5. **Integration with Major Platforms:** DigiLocker, myScheme, UMANG
6. **Consent-Based Architecture:** Privacy-focused design
7. **Developer-Friendly:** Extensive documentation, no-signup sandbox

### Critical Considerations

1. **Approval Required:** Production access needs government approval
2. **Use Case Validation:** Must demonstrate legitimate purpose
3. **API Provider Consent:** Individual APIs may need provider approval
4. **Rate Limits:** Usage quotas enforced
5. **Compliance Mandatory:** Strict adherence to terms required
6. **Variable Timelines:** 6-14 weeks for full integration

### Best Practices for Integration

1. **Start Early:** Account for approval timelines
2. **Define Clear Use Cases:** Essential for approval
3. **Test Thoroughly in Sandbox:** Free and unrestricted
4. **Document Everything:** Maintain integration records
5. **Monitor Continuously:** Track usage and errors
6. **Stay Compliant:** Follow all terms and conditions
7. **Plan for Scale:** Design for production volumes

---

## Official Resources and Links

### Primary Portals

- **Main Website:** https://www.apisetu.gov.in
- **API Directory:** https://directory.apisetu.gov.in
- **Partners Portal:** https://partners.apisetu.gov.in
- **Sandbox Environment:** https://sandbox.api-setu.in
- **Documentation:** https://docs.apisetu.gov.in

### Registration and Access

- **Sign Up:** https://partners.apisetu.gov.in/signup
- **Sign In:** https://partners.apisetu.gov.in/signin
- **Onboarding Guidelines:** https://negd.gov.in (search for API Setu)

### Documentation

- **Explore API Setu:** https://docs.apisetu.gov.in/document-central/explore-apisetu/
- **Terms of Use:** https://docs.apisetu.gov.in/document-central/terms-of-use/
- **SOP for Consumers:** https://cdn.apisetu.gov.in/portal/assets/sop-apisetu-v1.pdf
- **FAQ:** https://apisetu.gov.in/faq

### Specific Services

- **DigiLocker APIs:** https://apisetu.gov.in/digilocker
- **DigiLocker Issuer Spec:** https://cf-media.api-setu.in/resources/DigiLocker-Issuer-APISpecification-v1-13.pdf
- **DigiLocker Partner Spec:** https://cf-media.api-setu.in/resources/DigitalLocker-AuthorizedPartnerAPI-Specificationv2.2.pdf
- **myScheme APIs:** https://directory.apisetu.gov.in/api-collection/myscheme
- **myScheme Platform:** https://www.myscheme.gov.in

### Government Resources

- **Digital India - API Setu:** https://www.digitalindia.gov.in/initiative/api-setu/
- **Digital India Corporation:** https://dic.gov.in/initiative_digital/api-setu/
- **About API Setu:** https://apisetu.gov.in/aboutus
- **NeGD:** https://negd.gov.in

---

## Research Sources

This report is compiled from official government sources and documentation as of August 2026:

1. [About Us | APISetu](https://apisetu.gov.in/aboutus)
2. [Introduction — Explore API Setu documentation](https://docs.apisetu.gov.in/document-central/explore-apisetu/Introduction.html)
3. [API SETU - Digital India](https://www.digitalindia.gov.in/initiative/api-setu/)
4. [API Setu - Digital India Corporation](https://dic.gov.in/initiative_digital/api-setu/)
5. [API Directory: Get access to thousands of APIs | API Setu](https://directory.apisetu.gov.in/)
6. [Website of API Setu | National Portal of India](https://www.india.gov.in/category/science-it-communication/subcategory/information-technology/details/website-of-api-setu)
7. [Standard Operating Procedure (SOP) for consuming API through API Setu](https://cdn.apisetu.gov.in/portal/assets/sop-apisetu-v1.pdf)
8. [Sandbox — Explore API Setu documentation](https://docs.apisetu.gov.in/document-central/explore-apisetu/Sandbox.html)
9. [API Usage Limits — API Setu Terms of Use documentation](https://docs.apisetu.gov.in/document-central/terms-of-use/API%20Usage%20Limits.html)
10. [Access Restrictions — API Setu Terms of Use documentation](https://docs.apisetu.gov.in/document-central/terms-of-use/Access%20Restrictions.html)
11. [Permitted Use and Access — API Setu Terms of Use documentation](https://docs.apisetu.gov.in/document-central/terms-of-use/Permitted%20Use%20and%20Access.html)
12. [myScheme - Digital India](https://www.digitalindia.gov.in/initiative/myscheme/)
13. [myScheme Platform](https://www.myscheme.gov.in/)
14. [Digilocker | APISetu](https://apisetu.gov.in/digilocker)
15. [Integration guide — DigiLocker | Setu Docs](https://docs.setu.co/data/digilocker/quickstart)
16. [Issuer API Specification Version 1.13 May 2024](https://cf-media.api-setu.in/resources/DigiLocker-Issuer-APISpecification-v1-13.pdf)
17. [Authorized Partner API Specification Version 2.2 October 2022](https://cf-media.api-setu.in/resources/DigitalLocker-AuthorizedPartnerAPI-Specificationv2.2.pdf)
18. [Guidelines for Onboarding for API as a service provider](https://negd.gov.in/wp-content/uploads/2025/06/Guidelines-for-Onboarding-for-API-as-a-service-provider-v15-Rev-1-1.pdf)
19. [Use Cases — Explore API Setu documentation](https://docs.apisetu.gov.in/document-central/explore-apisetu/Use%20Cases.html)
20. [KYC Benefits With APISETU Gateway – APISetu Blog](https://blog.apisetu.gov.in/kyc-benefits-with-apisetu-gateway/)

---

**Report Prepared By:** AI Research Assistant
**Date:** August 23, 2026
**Version:** 1.0
**Classification:** Public Information from Official Government Sources

---

*This research report is based on publicly available information from official government sources. For the most current information, please refer to the official API Setu website at https://www.apisetu.gov.in*
