# API Setu Registration Guide
**For LAWTRIX Integration with myScheme & DigiLocker**

---

## Overview

API Setu is India's National Open API Platform that provides access to 8,036+ government APIs including:
- **myScheme** - 4,700+ government schemes
- **DigiLocker** - 300M+ documents (Aadhaar, PAN, licenses, certificates)
- **Aadhaar eKYC** - Identity verification
- **GSTN, PAN, VAHAN** - Business and vehicle verification

**Access**: FREE for approved use cases
**Timeline**: 1-2 weeks for approval

---

## Prerequisites

Before starting registration, gather these documents:

### Required Documents
1. **Organization PAN Card**
2. **GST Certificate**
3. **Certificate of Incorporation**
4. **Authority Letter** (signed by authorized signatory)
5. **Proof of Identity** (Aadhaar/PAN of authorized person)
6. **Valid Use Case** (see below)

### Use Case Document
Create a 1-2 page document describing:
- **Product**: LAWTRIX - Unified citizen action platform
- **Purpose**: Help citizens access government schemes, RTI, CPGRAMS, and civic services
- **APIs Needed**: myScheme, DigiLocker (and optionally others)
- **Data Usage**: User scheme eligibility, document verification for applications
- **User Consent**: Explicit consent collected before DigiLocker access
- **Compliance**: DPDP Act 2023, IT Act 2000
- **Expected Volume**: Initially 100-1000 requests/day, scaling to 10K+

---

## Step 1: Register on API Setu Partners Portal

1. **Go to**: https://partners.apisetu.gov.in/signup

2. **Fill Registration Form**:
   - Organization Name
   - Email (will be used for all communication)
   - Phone Number
   - Address
   - Industry: Technology / SaaS
   - Organization Type: Private Limited / Startup

3. **Upload Documents**:
   - PAN card
   - GST certificate
   - Incorporation certificate
   - Authority letter
   - ID proof

4. **Submit & Wait**:
   - You'll receive a confirmation email
   - API Setu team will review (1-3 business days)
   - They may request additional information

---

## Step 2: Access API Directory

Once approved:

1. **Login**: https://partners.apisetu.gov.in/login

2. **Browse API Directory**: https://directory.apisetu.gov.in/

3. **Find Required APIs**:
   - Search for "myScheme"
   - Search for "DigiLocker"
   - Review API specifications

---

## Step 3: Subscribe to APIs

1. **Navigate to API Details** (e.g., myScheme Ministry Wise Schemes Count)

2. **Click "Subscribe"**

3. **Select Environment**:
   - **Sandbox**: For testing (available immediately)
   - **Production**: For live use (requires approval)

4. **Submit Subscription Request**:
   - Provide use case summary
   - Expected API call volume
   - Purpose of integration

5. **Wait for Approval**:
   - Sandbox: Instant
   - Production: 3-7 business days

---

## Step 4: Test in Sandbox

### Sandbox Access (Immediate)

**Sandbox URL**: https://sandbox.api-setu.in

**No approval needed** - start testing immediately!

### Get Sandbox Credentials

1. Login to partners portal
2. Navigate to "My Applications"
3. Create new application
4. Select "Sandbox" environment
5. Copy credentials:
   - Client ID
   - Client Secret
   - API Key (if required)

### Test OAuth 2.0 Flow

```bash
# Get access token
curl -X POST https://sandbox.api-setu.in/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"

# Response:
# {
#   "access_token": "eyJhbGciOiJ...",
#   "token_type": "Bearer",
#   "expires_in": 3600
# }

# Use token to call API
curl -X GET "https://sandbox.api-setu.in/myscheme/v1/schemes?category=agriculture" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update LAWTRIX Config

Add to `chakravyuha/.env`:

```bash
# API Setu Sandbox (for testing)
APISETU_CLIENT_ID=your_sandbox_client_id
APISETU_CLIENT_SECRET=your_sandbox_client_secret
APISETU_SANDBOX=true  # true for sandbox, false for production
```

---

## Step 5: Request Production Access

Once sandbox testing is successful:

1. **Go to "My Subscriptions"** in partners portal

2. **Click "Request Production Access"**

3. **Provide Production Details**:
   - Detailed use case
   - Test results from sandbox
   - Expected daily/monthly API calls
   - Security measures implemented
   - DPDP Act compliance attestation

4. **Wait for Approval**: 5-10 business days

5. **Receive Production Credentials**:
   - Production Client ID
   - Production Client Secret
   - Rate limits (typically 1000-10000 requests/day)

---

## Step 6: Deploy to Production

### Update Production Config

Update `chakravyuha/.env.production`:

```bash
# API Setu Production
APISETU_CLIENT_ID=your_production_client_id
APISETU_CLIENT_SECRET=your_production_client_secret
APISETU_SANDBOX=false

# DigiLocker (when approved)
DIGILOCKER_CLIENT_ID=your_digilocker_client_id
DIGILOCKER_CLIENT_SECRET=your_digilocker_client_secret
DIGILOCKER_REDIRECT_URI=https://lawtrix.app/auth/digilocker/callback
```

### Test Production Integration

```python
# Test in Python
from backend.services.scheme_provider import get_scheme_router

async def test_api_setu():
    router = get_scheme_router()
    schemes, source = await router.get_schemes({"category": "agriculture"})
    print(f"Found {len(schemes)} schemes from {source}")
    # Expected: source = "api_live" if API Setu working
```

---

## DigiLocker Specific Steps

DigiLocker requires additional setup:

### 1. Register Application

1. Go to: https://digilocker.meripehchaan.gov.in/
2. Login with existing account or create one
3. Navigate to "Partner" section
4. Register your application

### 2. Configure OAuth Callback

**Redirect URI**: `https://lawtrix.app/auth/digilocker/callback`

Must be HTTPS in production!

### 3. Request Document Access Scopes

Select required document types:
- `aadhaar` - Aadhaar card
- `pan` - PAN card
- `driving_license` - DL
- `vehicle_rc` - Vehicle registration
- `education` - Educational certificates

### 4. User Consent Flow

DigiLocker requires explicit user consent:

1. User clicks "Connect DigiLocker" in LAWTRIX
2. Redirect to DigiLocker consent page
3. User authorizes document access
4. DigiLocker redirects back with authorization code
5. LAWTRIX exchanges code for access token
6. Fetch documents on behalf of user

---

## Rate Limits & Best Practices

### API Setu Rate Limits

**Sandbox**: 100 requests/hour (for testing)
**Production**: Depends on subscription (typically 1000-10000/day)

### Best Practices

1. **Cache Aggressively**:
   - Scheme data: 24-hour TTL
   - User documents: Session-based cache
   - Never cache sensitive data on disk

2. **Handle Rate Limits**:
   ```python
   # Check rate limit before calling
   allowed, remaining = await cache.check_rate_limit(user_id)
   if not allowed:
       return {"error": "Rate limit exceeded"}
   ```

3. **Graceful Degradation**:
   - API Setu fails → fall back to local schemes
   - DigiLocker fails → allow manual upload

4. **Error Handling**:
   - Log all API errors
   - Never expose API keys in error messages
   - Show user-friendly messages

5. **Security**:
   - Never log access tokens
   - Rotate credentials every 90 days
   - Use HTTPS only
   - Implement CSRF protection for OAuth callbacks

---

## Troubleshooting

### "Unauthorized" Error

**Cause**: Invalid or expired credentials
**Fix**:
1. Check CLIENT_ID and CLIENT_SECRET are correct
2. Regenerate access token
3. Verify subscription is active

### "Forbidden" Error

**Cause**: API not subscribed or production not approved
**Fix**:
1. Check subscription status in partners portal
2. Ensure production access granted
3. Verify use case matches subscription

### "Rate Limit Exceeded"

**Cause**: Too many requests
**Fix**:
1. Implement caching (24-hour TTL for schemes)
2. Add rate limiting on your side
3. Request higher limits from API Setu

### OAuth Flow Fails

**Cause**: Redirect URI mismatch
**Fix**:
1. Verify REDIRECT_URI exactly matches registered URI
2. Must be HTTPS in production
3. Check for trailing slashes

---

## Timeline Summary

| Phase | Duration | Action |
|-------|----------|--------|
| **Registration** | 1-3 days | Submit documents, get portal access |
| **Sandbox Testing** | Immediate | Test integration with sandbox |
| **Production Request** | 5-10 days | Submit production access request |
| **Production Deploy** | 1 day | Update config, deploy |
| **Total** | ~2 weeks | From registration to production |

---

## Contacts

### API Setu Support
- **Email**: support@apisetu.gov.in
- **Portal**: https://partners.apisetu.gov.in/support
- **Documentation**: https://docs.apisetu.gov.in/

### DigiLocker Support
- **Email**: support@digitalindia.gov.in
- **Documentation**: https://digilocker.gov.in/assets/docs/

---

## Next Steps for LAWTRIX

1. ✅ **Week 1**: Start registration process (submit documents)
2. ✅ **Week 1**: Test with sandbox while waiting for approval
3. **Week 2**: Receive production approval
4. **Week 2**: Deploy with live API integration
5. **Week 3**: Monitor usage, optimize caching
6. **Week 4**: Expand to additional APIs (Aadhaar eKYC, PAN verification)

---

## Checklist

- [ ] Gather all required documents (PAN, GST, incorporation cert, etc.)
- [ ] Prepare use case document (1-2 pages)
- [ ] Register on API Setu partners portal
- [ ] Subscribe to myScheme API
- [ ] Subscribe to DigiLocker API
- [ ] Get sandbox credentials
- [ ] Update `.env` with sandbox credentials
- [ ] Test sandbox integration
- [ ] Request production access
- [ ] Wait for production approval (5-10 days)
- [ ] Update `.env.production` with production credentials
- [ ] Deploy to production
- [ ] Monitor API usage and rate limits
- [ ] Set up alerts for API failures

---

**Start Date**: ________________
**Expected Production Date**: ________________

**Notes**:
- Keep all credentials in environment variables (never commit to git)
- Document any API changes or issues
- Review API Setu terms of use regularly
