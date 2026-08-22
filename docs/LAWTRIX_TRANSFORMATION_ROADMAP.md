# LAWTRIX TRANSFORMATION ROADMAP
## From Civic Workflows to Unified Citizen Action Platform

**Date**: 2026-08-23
**Version**: 1.0
**Status**: COMPREHENSIVE GAP ANALYSIS + IMPLEMENTATION PLAN

---

## EXECUTIVE SUMMARY

### Current State
The LAWTRIX repository contains **two distinct applications**:
1. **LAWTRIX Core** - MSME payment compliance tool (production-capable)
2. **Chakravyuha** - Comprehensive civic/legal action assistant (feature-rich)

### Critical Finding
**Most features from the transformation requirements ALREADY EXIST in Chakravyuha**. This is NOT a rebuild project—it's an enhancement and unification effort.

### Research Results (Government APIs)
✅ **myScheme**: 4,700+ schemes available via API Setu (requires registration)
✅ **API Setu**: 8,036 government APIs, free for approved use cases, sandbox ready
✅ **DigiLocker**: 300M+ documents, OAuth 2.0, commercial integration available
⚠️ **data.gov.in**: 100K+ APIs but limited real-time utility

### Transformation Strategy
**Build on Chakravyuha foundation**, enhance with:
- Unified citizen case state abstraction
- Live government API integration
- Enhanced UX for citizen-facing workflows
- Production hardening (auth, persistence, scale)

### Timeline
**4-6 weeks** to production-ready unified platform (vs 6+ months if rebuilding)

---

## PART 1: ARCHITECTURAL FOUNDATIONS

### 1.1 Current Architecture (Chakravyuha)

```
USER INPUT (text/voice)
    ↓
VOICE SERVICE (Sarvam ASR + cascade) ✓
    ↓
ORCHESTRATOR ✓
    ↓
INTENT CLASSIFIER ⚠️
    ↓
ISOLATED SERVICES ⚠️
├── RTI Assistant ✓
├── CPGRAMS Service ✓
├── Scheme Engine ✓
├── Legal Service (RAG) ✓
├── Case Service (CRUD) ⚠️
    ↓
OPENCLAW Browser Automation ✓
├── Human Gates ✓
├── OTP/CAPTCHA Gates ✓
├── Session Resumability ✓
    ↓
RESPONSE ENGINE ✓
```

**Issues**:
- No unified citizen case state
- Services operate independently
- No automatic workflow handoff
- Case tracking is basic CRUD only

### 1.2 Target Architecture

```
CITIZEN INPUT (text/voice/document/image)
    ↓
INPUT NORMALIZATION (ASR/OCR/extraction)
    ↓
UNIFIED INTENT ROUTER (action-first)
    ↓
═══════════════════════════════════════
    CITIZEN CASE STATE ← NEW CORE
═══════════════════════════════════════
    ├─ input (raw, normalized, attachments)
    ├─ intent (category, confidence, reasoning)
    ├─ problem (summary, facts, outcome)
    ├─ profile (demographics, jurisdiction)
    ├─ workflow (name, status, step, fields)
    ├─ evidence (documents, sources)
    ├─ action (type, authority, portal)
    ├─ automation (mode, state, gates)
    ├─ consent (data, automation, submission)
    ├─ submission (status, reference, tracking)
    └─ provenance (source, verified, confidence)
    ↓
WORKFLOW ENGINE
├── RTI ✓
├── CPGRAMS ✓
├── Schemes ✓ → ENHANCE with live data
├── Consumer → BUILD full workflow
├── Tenant → BUILD full workflow
├── Labour → BUILD full workflow
    ↓
AUTHORITY/SERVICE RESOLUTION
├── RTI authority hints ✓
├── CPGRAMS routing ✓
└── Generic resolver → BUILD
    ↓
ACTION/DOCUMENT ENGINE ✓
├── FIR, notices, complaints ✓
└── Form schemas → BUILD generic mapper
    ↓
AUTOMATION PLANNER
├── API adapters → BUILD
├── Browser adapters ✓ (OpenClaw)
└── Human checkpoints ✓
    ↓
CASE TRACKER
├── Timeline → BUILD
├── Status updates → BUILD
└── Reminders → BUILD
```

### 1.3 Core Abstraction: CitizenCase Model

**New unified schema** (Pydantic, immutable):

```python
class CitizenCase(BaseModel):
    """Unified case state spanning all civic/legal workflows."""
    model_config = {"frozen": True}

    # Identity
    case_id: str
    created_at: datetime
    updated_at: datetime
    citizen_id: str | None = None

    # Input
    input: CaseInput
    # ├─ raw_text: str
    # ├─ transcript: str | None
    # ├─ language: str
    # └─ attachments: list[Attachment]

    # Intent
    intent: CaseIntent
    # ├─ category: IntentCategory (rti/cpgrams/schemes/consumer/tenant/labour/legal)
    # ├─ subcategory: str
    # ├─ confidence: float
    # └─ reasoning: str

    # Problem
    problem: CaseProblem
    # ├─ summary: str
    # ├─ facts: list[Fact]
    # └─ requested_outcome: str

    # Profile
    profile: CitizenProfile
    # ├─ age: int | None
    # ├─ occupation: str | None
    # ├─ state: str | None
    # ├─ district: str | None
    # └─ ... other demographics

    # Jurisdiction
    jurisdiction: Jurisdiction
    # ├─ state: str | None
    # ├─ district: str | None
    # ├─ authority: str | None
    # ├─ authority_confidence: float
    # └─ authority_verified: bool

    # Workflow
    workflow: WorkflowState
    # ├─ name: str (rti/cpgrams/schemes/etc.)
    # ├─ status: WorkflowStatus
    # ├─ step: str
    # ├─ required_fields: list[str]
    # └─ missing_fields: list[str]

    # Evidence
    evidence: CaseEvidence
    # ├─ documents: list[Document]
    # ├─ extracted_facts: list[Fact]
    # └─ source_documents: list[str]

    # Documents
    documents: CaseDocuments
    # ├─ generated: list[GeneratedDocument]
    # └─ user_provided: list[UserDocument]

    # Action
    action: CaseAction
    # ├─ action_type: ActionType
    # ├─ target_authority: str | None
    # ├─ target_portal: str | None
    # └─ target_api: str | None

    # Automation
    automation: AutomationState
    # ├─ mode: AutomationMode (api/browser/guided/manual)
    # ├─ capability: str | None
    # ├─ current_state: AutomationStateEnum
    # ├─ blocked_reason: str | None
    # └─ pending_user_action: str | None

    # Consent
    consent: CaseConsent
    # ├─ data_sharing: bool
    # ├─ document_access: bool
    # ├─ automation: bool
    # └─ final_submission: bool

    # Submission
    submission: SubmissionState
    # ├─ status: SubmissionStatus
    # ├─ reference_id: str | None
    # ├─ submitted_at: datetime | None
    # ├─ authority: str | None
    # └─ portal: str | None

    # Tracking
    tracking: TrackingState
    # ├─ next_check: datetime | None
    # ├─ reminders: list[Reminder]
    # └─ status_history: list[StatusChange]

    # Provenance
    provenance: Provenance
    # ├─ source: str
    # ├─ source_url: str | None
    # ├─ verified_at: datetime | None
    # └─ confidence: float
```

**Benefits**:
- Single source of truth across all workflows
- Portable between services
- Enables workflow handoff
- Supports resume/recovery
- Audit trail built-in

---

## PART 2: GOVERNMENT API INTEGRATION

### 2.1 API Setu Integration Architecture

**Provider Abstraction**:

```python
class SchemeProvider(ABC):
    """Abstract base for scheme data sources."""

    @abstractmethod
    def get_schemes(self, filters: dict) -> list[Scheme]:
        """Get schemes matching filters."""
        pass

    @abstractmethod
    def check_eligibility(self, scheme_id: str, profile: dict) -> EligibilityResult:
        """Check eligibility for a scheme."""
        pass

    @abstractmethod
    def get_scheme_details(self, scheme_id: str) -> Scheme:
        """Get full scheme details."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is currently available."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return source type (local/api/live)."""
        pass
```

**Concrete Implementations**:

```python
class LocalVerifiedProvider(SchemeProvider):
    """Local JSON-based verified schemes (current 3 schemes)."""
    source_type = "local"
    is_available = True  # Always available as fallback

class APISetuMySchemeProvider(SchemeProvider):
    """Live integration with myScheme via API Setu."""
    source_type = "live_api"

    def __init__(self):
        self.client_id = os.getenv("APISETU_CLIENT_ID")
        self.client_secret = os.getenv("APISETU_CLIENT_SECRET")
        self.oauth_token = None
        self.sandbox_mode = os.getenv("APISETU_SANDBOX", "true") == "true"

    @property
    def is_available(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_schemes(self, filters: dict) -> list[Scheme]:
        if not self.is_available:
            raise ProviderUnavailableError()

        # OAuth 2.0 flow
        if not self.oauth_token:
            self.oauth_token = self._get_access_token()

        # Call myScheme API
        url = self._get_endpoint("/schemes/search")
        response = httpx.get(url, headers=self._auth_headers(), params=filters)

        # Transform API response to internal Scheme model
        return [self._transform_scheme(s) for s in response.json()["schemes"]]

class GovernmentOpenDataProvider(SchemeProvider):
    """data.gov.in schemes API (supplementary)."""
    source_type = "open_data"

    @property
    def is_available(self) -> bool:
        # Always available (free API)
        return True
```

**Router with Fallback**:

```python
class SchemeProviderRouter:
    """Route to best available provider with fallback."""

    def __init__(self):
        self.providers = [
            APISetuMySchemeProvider(),      # Try live first
            GovernmentOpenDataProvider(),   # Fallback to open data
            LocalVerifiedProvider(),        # Always-available fallback
        ]

    def get_schemes(self, filters: dict) -> tuple[list[Scheme], str]:
        """Get schemes from first available provider."""
        for provider in self.providers:
            if provider.is_available:
                try:
                    schemes = provider.get_schemes(filters)
                    return schemes, provider.source_type
                except Exception as e:
                    logger.warning(f"{provider.source_type} failed: {e}")
                    continue

        return [], "none"
```

### 2.2 DigiLocker Integration Architecture

**Document Provider Abstraction**:

```python
class DocumentProvider(ABC):
    """Abstract base for document sources."""

    @abstractmethod
    async def list_documents(self, user_consent_token: str) -> list[DocumentMetadata]:
        """List available documents for user."""
        pass

    @abstractmethod
    async def retrieve_document(
        self,
        doc_uri: str,
        user_consent_token: str
    ) -> Document:
        """Retrieve specific document."""
        pass

    @abstractmethod
    def get_consent_url(self, callback_url: str, scope: list[str]) -> str:
        """Generate OAuth consent URL."""
        pass

class DigiLockerProvider(DocumentProvider):
    """DigiLocker integration via API Setu."""

    def __init__(self):
        self.client_id = os.getenv("DIGILOCKER_CLIENT_ID")
        self.client_secret = os.getenv("DIGILOCKER_CLIENT_SECRET")
        self.redirect_uri = os.getenv("DIGILOCKER_REDIRECT_URI")

    def get_consent_url(self, callback_url: str, scope: list[str]) -> str:
        """Generate OAuth 2.0 consent URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": generate_state_token(),
            "scope": " ".join(scope),  # e.g., ["aadhaar", "pan", "driving_license"]
        }
        return f"https://digilocker.meripehchaan.gov.in/oauth2/authorize?{urlencode(params)}"

    async def list_documents(self, user_consent_token: str) -> list[DocumentMetadata]:
        """List user's documents after OAuth consent."""
        headers = {"Authorization": f"Bearer {user_consent_token}"}
        response = await httpx.get(
            "https://api.digitallocker.gov.in/public/oauth2/1/files",
            headers=headers
        )
        return [self._parse_metadata(doc) for doc in response.json()["items"]]

    async def retrieve_document(self, doc_uri: str, user_consent_token: str) -> Document:
        """Retrieve and verify digitally-signed document."""
        headers = {"Authorization": f"Bearer {user_consent_token}"}
        response = await httpx.get(
            f"https://api.digitallocker.gov.in/public/oauth2/1/file/{doc_uri}",
            headers=headers
        )

        # Verify digital signature
        if not self._verify_signature(response.content):
            raise DocumentVerificationError()

        return Document(
            uri=doc_uri,
            content=response.content,
            verified=True,
            issuer=response.headers.get("X-Issuer"),
            timestamp=datetime.now(),
        )

class UserUploadProvider(DocumentProvider):
    """User-uploaded documents (current implementation)."""
    # ... existing upload logic
```

### 2.3 Integration Phases

**Phase 1: Sandbox Testing (Week 1)**
- ✅ Register with API Setu partners portal
- ✅ Access sandbox environment (immediate)
- ✅ Test myScheme API integration
- ✅ Test DigiLocker OAuth flow
- ✅ Implement provider abstraction
- ✅ Unit tests with sandbox data

**Phase 2: Production Registration (Week 1-2)**
- Submit use case documentation
- Wait for API Setu approval (1-2 weeks)
- Generate production credentials
- Security audit of OAuth implementation

**Phase 3: Production Deployment (Week 3)**
- Deploy with live API access
- Monitor rate limits
- Implement caching (24-hour TTL for schemes)
- Add fallback to local provider on API failure

**Phase 4: Expansion (Week 4+)**
- Add more document types (education, vehicle, insurance)
- Explore additional API Setu services (Aadhaar eKYC, PAN verification)
- Integrate VAHAN/Sarathi for transport documents

---

## PART 3: WORKFLOW ENHANCEMENTS

### 3.1 Unified Intent Router

**Current**: `backend/services/classifier.py` (basic classification)

**Target**: Action-first router with automatic handoff

```python
class UnifiedIntentRouter:
    """Action-first intent classification with auto-handoff."""

    INTENT_MAP = {
        "information_request": "rti",
        "government_service_grievance": "cpgrams",
        "scheme_eligibility": "schemes",
        "rights_guidance_tenant": "tenant",
        "rights_guidance_consumer": "consumer",
        "rights_guidance_labour": "labour",
        "criminal_legal_incident": "legal",
        "general_civic_information": "guidance",
    }

    def route(self, user_input: str, context: dict) -> RouteResult:
        """Classify intent and recommend workflow."""

        # Extract action signals
        action_signals = self._extract_actions(user_input)
        # "want records" → information_request
        # "complaint", "grievance" → government_service_grievance
        # "eligible", "scheme" → scheme_eligibility
        # "landlord", "rent", "deposit" → rights_guidance_tenant
        # "salary", "employer", "terminated" → rights_guidance_labour
        # "defective", "refund", "seller" → rights_guidance_consumer

        # Use LLM for ambiguous cases
        if not action_signals or self._is_ambiguous(action_signals):
            intent = self._llm_classify(user_input, context)
        else:
            intent = self._rule_based_classify(action_signals)

        # Confidence threshold for auto-handoff
        if intent.confidence >= 0.75:
            workflow = self.INTENT_MAP.get(intent.category)
            auto_handoff = True
        else:
            workflow = None
            auto_handoff = False

        return RouteResult(
            intent=intent.category,
            confidence=intent.confidence,
            reasoning=intent.reasoning,
            workflow=workflow,
            auto_handoff=auto_handoff,
            clarification_needed=not auto_handoff,
        )
```

### 3.2 Workflow Contract

**Standardize all workflows**:

```python
class WorkflowHandler(ABC):
    """Standard interface for all workflows."""

    @abstractmethod
    def prepare(self, case: CitizenCase) -> PrepareResult:
        """
        Analyze case and return:
        - required_fields: list[str]
        - known_fields: dict
        - missing_fields: list[str]
        - warnings: list[str]
        - confidence: float
        - authority: str | None
        - draft: Document | None
        - action_options: list[ActionOption]
        """
        pass

    @abstractmethod
    def validate(self, case: CitizenCase) -> ValidationResult:
        """
        Return:
        - ready: bool
        - blockers: list[str]
        - warnings: list[str]
        """
        pass

    @abstractmethod
    def preview_action(self, case: CitizenCase) -> ActionPreview:
        """
        Return human-readable preview:
        - target_authority: str
        - action_type: str
        - documents_to_submit: list[str]
        - data_shared: dict
        - fees: str | None
        - expected_outcome: str
        - risks_warnings: list[str]
        - what_happens_next: str
        """
        pass

    @abstractmethod
    def requires_confirmation(self, case: CitizenCase) -> bool:
        """Check if explicit user confirmation needed."""
        pass

    @abstractmethod
    async def execute(self, case: CitizenCase) -> ExecutionResult:
        """
        Execute only if authorized.
        Return:
        - status: ExecutionStatus
        - reference_id: str | None
        - message: str
        - next_steps: list[str]
        """
        pass

    @abstractmethod
    async def track(self, case: CitizenCase) -> TrackingResult:
        """
        Return current status:
        - status: str
        - last_updated: datetime
        - next_check: datetime | None
        - history: list[StatusChange]
        """
        pass
```

**Implement for each workflow**:
- `RTIWorkflowHandler`
- `CPGRAMSWorkflowHandler`
- `SchemeWorkflowHandler`
- `ConsumerWorkflowHandler`
- `TenantWorkflowHandler`
- `LabourWorkflowHandler`

### 3.3 Enhanced Workflows

#### Consumer Workflow (NEW)

```python
class ConsumerWorkflowHandler(WorkflowHandler):
    """Consumer complaint workflow."""

    def prepare(self, case: CitizenCase) -> PrepareResult:
        # Extract: product/service, seller, issue, amount, proof
        # Determine forum: Consumer Forum (district/state/national based on amount)
        # Check jurisdiction
        # Generate draft complaint
        # Suggest evidence needed

    def preview_action(self, case: CitizenCase) -> ActionPreview:
        return ActionPreview(
            target_authority="District Consumer Forum, {district}",
            action_type="Consumer Complaint",
            documents_to_submit=["Invoice", "Photos", "Communication"],
            data_shared={"name": "...", "address": "...", "complaint": "..."},
            fees="INR 100-200 (based on claim amount)",
            expected_outcome="Hearing scheduled within 90 days",
            risks_warnings=["Must appear for hearings", "Legal representation optional"],
            what_happens_next="File complaint → Notice to seller → Hearing → Order",
        )
```

#### Tenant Workflow (NEW)

```python
class TenantWorkflowHandler(WorkflowHandler):
    """Tenant rights workflow."""

    def prepare(self, case: CitizenCase) -> PrepareResult:
        # Requires: state (rental laws are state-specific!)
        # Extract: issue (deposit, eviction, maintenance, rent increase)
        # Determine: Rent Control Authority or Civil Court
        # Check: rent agreement terms
        # Generate: legal notice or complaint

    def preview_action(self, case: CitizenCase) -> ActionPreview:
        if case.jurisdiction.state is None:
            return ActionPreview(
                blockers=["State/UT required - rental laws vary by state"],
                next_steps=["Specify your state to get accurate guidance"],
            )

        return ActionPreview(
            target_authority=f"Rent Control Authority, {case.jurisdiction.state}",
            action_type="Deposit Refund Notice",
            documents_to_submit=["Rent Agreement", "Deposit Receipt", "Vacate Notice"],
            # ... rest of preview
        )
```

#### Labour Workflow (NEW)

```python
class LabourWorkflowHandler(WorkflowHandler):
    """Labour rights workflow."""

    def prepare(self, case: CitizenCase) -> PrepareResult:
        # Extract: issue (unpaid wages, termination, harassment, PF, ESI)
        # Determine forum:
        #   - Labour Commissioner (wages, hours)
        #   - EPFO (provident fund)
        #   - ESIC (insurance)
        #   - Labour Court (termination disputes)
        # Check: employment type, industry, state
        # Generate: complaint to Labour Commissioner
```

### 3.4 Form-Filling Engine (Generic)

**FormSchema Definition**:

```python
class FormSchema(BaseModel):
    """Generic form schema for any government portal."""

    form_id: str
    portal_id: str
    fields: list[FormField]

class FormField(BaseModel):
    field_id: str
    label: str
    type: FieldType  # text/number/date/select/file/checkbox
    required: bool
    source: FieldSource  # case_input/user_profile/document/manual
    value: Any | None = None
    confidence: float | None = None
    validation: FieldValidation | None = None
    editable: bool = True
    sensitive: bool = False
    portal_selector: str | None = None  # CSS/XPath selector
    document_dependency: str | None = None
```

**Deterministic Mapper**:

```python
class FormMapper:
    """Map CitizenCase to FormSchema."""

    FIELD_MAPPING = {
        # Profile fields
        "applicant_name": lambda case: case.profile.name,
        "applicant_age": lambda case: case.profile.age,
        "applicant_occupation": lambda case: case.profile.occupation,
        "applicant_state": lambda case: case.jurisdiction.state,
        "applicant_district": lambda case: case.jurisdiction.district,

        # Case fields
        "complaint_subject": lambda case: case.problem.summary,
        "complaint_details": lambda case: case.problem.facts_narrative,
        "requested_action": lambda case: case.problem.requested_outcome,

        # Documents
        "identity_proof": lambda case: case.documents.get_by_type("identity"),
        "address_proof": lambda case: case.documents.get_by_type("address"),
    }

    def map(self, case: CitizenCase, form_schema: FormSchema) -> FilledForm:
        """Map case data to form fields deterministically."""
        filled_fields = []

        for field in form_schema.fields:
            if field.field_id in self.FIELD_MAPPING:
                mapper_fn = self.FIELD_MAPPING[field.field_id]
                value = mapper_fn(case)
                confidence = 1.0 if value else 0.0
            else:
                value = None
                confidence = 0.0

            filled_fields.append(FilledFormField(
                field_id=field.field_id,
                value=value,
                confidence=confidence,
                source=field.source,
                editable=field.editable,
            ))

        return FilledForm(
            form_id=form_schema.form_id,
            fields=filled_fields,
            ready_to_submit=all(f.value for f in filled_fields if f.required),
        )
```

---

## PART 4: CASE TRACKING & INTELLIGENCE

### 4.1 Case Timeline

**Schema**:

```python
class CaseTimeline(BaseModel):
    case_id: str
    events: list[TimelineEvent]

class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: EventType  # created/updated/submitted/status_changed/reminder
    actor: str  # system/user/authority
    description: str
    details: dict | None = None
```

**Service**:

```python
class CaseTracker:
    """Track case lifecycle and status."""

    def add_event(self, case_id: str, event: TimelineEvent):
        # Persist to database
        # Update case.tracking.status_history

    def get_timeline(self, case_id: str) -> CaseTimeline:
        # Retrieve all events for case

    def schedule_reminder(self, case_id: str, reminder: Reminder):
        # Add to background job queue
        # Send notification when due

    async def check_status(self, case: CitizenCase) -> StatusUpdate:
        """Poll external portal for status update."""
        if case.workflow.name == "cpgrams":
            # Hit CPGRAMS API with reference_id
            status = await self._check_cpgrams_status(case.submission.reference_id)
        elif case.workflow.name == "rti":
            # Check RTI portal (if API available)
            status = await self._check_rti_status(case.submission.reference_id)
        else:
            status = None

        if status:
            self.add_event(case.case_id, TimelineEvent(
                timestamp=datetime.now(),
                event_type="status_changed",
                actor="system",
                description=f"Status updated: {status.current_status}",
                details=status.model_dump(),
            ))

        return status
```

### 4.2 Document Intelligence

**OCR Pipeline**:

```python
class DocumentIntelligence:
    """Extract structured data from uploaded documents."""

    async def process_document(self, file: UploadFile) -> ProcessedDocument:
        # 1. Classify document type
        doc_type = await self._classify(file)

        # 2. OCR extraction
        if doc_type in ["pdf", "image"]:
            text = await self._ocr(file)
        else:
            text = await file.read()

        # 3. Extract structured facts
        facts = await self._extract_facts(text, doc_type)

        # 4. Map to workflow
        workflow_hint = self._suggest_workflow(doc_type, facts)

        return ProcessedDocument(
            doc_type=doc_type,
            raw_text=text,
            extracted_facts=facts,
            workflow_hint=workflow_hint,
            confidence=0.8,  # Based on OCR quality
            requires_verification=True,  # Never auto-trust OCR
        )

    async def _classify(self, file: UploadFile) -> str:
        """Classify document type."""
        # Use filename, MIME type, or LLM vision model
        # Examples: rent_agreement, salary_slip, invoice, government_notice

    async def _ocr(self, file: UploadFile) -> str:
        """Extract text via OCR."""
        # Use Tesseract, Google Vision, or Azure Form Recognizer

    async def _extract_facts(self, text: str, doc_type: str) -> dict:
        """Extract structured information."""
        if doc_type == "rent_agreement":
            return {
                "landlord_name": extract_pattern(text, "Landlord:(.+)"),
                "tenant_name": extract_pattern(text, "Tenant:(.+)"),
                "monthly_rent": extract_amount(text),
                "deposit_amount": extract_deposit(text),
                "start_date": extract_date(text, "from"),
                "address": extract_address(text),
            }
        elif doc_type == "salary_slip":
            return {
                "employer_name": extract_company(text),
                "employee_name": extract_employee(text),
                "month": extract_month(text),
                "gross_salary": extract_amount(text, "Gross"),
                "deductions": extract_deductions(text),
                "net_salary": extract_amount(text, "Net"),
            }
        # ... more document types
```

### 4.3 Document Wallet

**Secure Storage**:

```python
class DocumentWallet:
    """Secure document storage with consent management."""

    def __init__(self):
        self.storage = S3Storage()  # or encrypted filesystem
        self.consent_db = ConsentDatabase()

    async def store_document(
        self,
        citizen_id: str,
        document: bytes,
        doc_type: str,
        metadata: dict,
        consent: DocumentConsent,
    ) -> StoredDocument:
        """Store document with explicit consent."""

        # Validate consent
        if not consent.storage_consent:
            raise ConsentRequiredError()

        # Encrypt document
        encrypted = self._encrypt(document)

        # Store with metadata
        doc_id = str(uuid.uuid4())
        storage_key = f"{citizen_id}/{doc_type}/{doc_id}"

        await self.storage.put(storage_key, encrypted)

        # Record consent
        await self.consent_db.record_consent(
            doc_id=doc_id,
            citizen_id=citizen_id,
            consent=consent,
            expires_at=consent.expiry_date,
        )

        return StoredDocument(
            doc_id=doc_id,
            doc_type=doc_type,
            stored_at=datetime.now(),
            expires_at=consent.expiry_date,
            can_share=consent.sharing_consent,
        )

    async def retrieve_document(
        self,
        doc_id: str,
        requester: str,
        purpose: str,
    ) -> bytes:
        """Retrieve document with consent check."""

        # Check consent
        consent = await self.consent_db.get_consent(doc_id)
        if not self._check_consent(consent, requester, purpose):
            raise ConsentDeniedError()

        # Retrieve and decrypt
        encrypted = await self.storage.get(consent.storage_key)
        document = self._decrypt(encrypted)

        # Audit log
        await self.consent_db.log_access(
            doc_id=doc_id,
            requester=requester,
            purpose=purpose,
            timestamp=datetime.now(),
        )

        return document
```

---

## PART 5: FRONTEND TRANSFORMATION

### 5.1 Decision: Use Chakravyuha-UI (Next.js 16)

**Rationale**:
- ✅ Modern stack (Next.js 16.2.1, React 19, Tailwind 4)
- ✅ Already integrated with Chakravyuha backend
- ✅ Server components + client components support
- ✅ Better performance than LAWTRIX React frontend

**Deprecate**: LAWTRIX frontend (`frontend/` with React + Vite)

### 5.2 UX Redesign Principles

**Action-First Home Screen**:

```tsx
// app/page.tsx (Next.js 16 App Router)

export default function HomePage() {
  return (
    <main>
      <Hero>
        <h1>What can we help you with today?</h1>
        <SearchBar placeholder="Describe your problem or ask a question" />
        <VoiceButton>Or speak instead</VoiceButton>
      </Hero>

      <QuickActions>
        <ActionCard
          icon={<DocumentIcon />}
          title="Get public records"
          description="File an RTI application"
          onClick={() => router.push('/workflows/rti')}
        />
        <ActionCard
          icon={<ComplaintIcon />}
          title="Report a problem"
          description="Government service complaint"
          onClick={() => router.push('/workflows/cpgrams')}
        />
        <ActionCard
          icon={<BenefitsIcon />}
          title="Find government schemes"
          description="Check eligibility"
          onClick={() => router.push('/workflows/schemes')}
        />
        <ActionCard
          icon={<RightsIcon />}
          title="Know your rights"
          description="Consumer, tenant, or labour"
          onClick={() => router.push('/workflows/rights')}
        />
      </QuickActions>

      <Examples>
        <ExampleChip>"My road hasn't been repaired"</ExampleChip>
        <ExampleChip>"I want municipal budget records"</ExampleChip>
        <ExampleChip>"My landlord won't return deposit"</ExampleChip>
        <ExampleChip>"Am I eligible for PM-SYM?"</ExampleChip>
      </Examples>
    </main>
  )
}
```

**Workflow Visual Language**:

```tsx
// Common progress indicator for all workflows

<WorkflowProgress steps={[
  { label: "Understand", status: "completed" },
  { label: "Details", status: "current" },
  { label: "Review", status: "pending" },
  { label: "Action", status: "pending" },
]} />
```

**Guided Conversation UI**:

```tsx
// Conversational workflow with auto-handoff

<Chat>
  <UserMessage>My municipality hasn't repaired the road</UserMessage>
  <SystemMessage>
    Got it. This sounds like a government service grievance.
    I'll help you prepare a complaint for CPGRAMS.
    <Button>Continue</Button>
  </SystemMessage>

  {/* Auto-transitions to CPGRAMS workflow */}
  <CPGRAMSWorkflow autoStart={true} initialProblem="..." />
</Chat>
```

### 5.3 Accessibility Requirements

- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Screen reader support (ARIA labels, semantic HTML)
- ✅ Focus states (visible outlines)
- ✅ Color contrast (WCAG AA minimum)
- ✅ Mobile-responsive (touch targets ≥44px)
- ✅ Voice alternative (speak instead of type)
- ✅ Error messages (clear, actionable)
- ✅ Form validation (inline feedback)

---

## PART 6: PRODUCTION HARDENING

### 6.1 Authentication & Authorization

**Currently**: None

**Required**:

```python
# backend/auth/auth.py

class AuthService:
    """JWT-based authentication."""

    async def register(self, phone: str, name: str) -> User:
        # Send OTP
        # Verify OTP
        # Create user

    async def login(self, phone: str) -> LoginResult:
        # Send OTP
        # Return session token

    async def verify_otp(self, phone: str, otp: str) -> AuthToken:
        # Verify OTP
        # Generate JWT

    def get_current_user(self, token: str) -> User:
        # Decode JWT
        # Return user
```

**Middleware**:

```python
# Protect endpoints

@router.get("/api/cases")
async def get_cases(current_user: User = Depends(get_current_user)):
    return case_service.get_user_cases(current_user.id)
```

### 6.2 Persistence

**Current**: In-memory (sessions, cases)

**Required**: PostgreSQL

**Schema**:

```sql
CREATE TABLE citizens (
    id UUID PRIMARY KEY,
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cases (
    case_id UUID PRIMARY KEY,
    citizen_id UUID REFERENCES citizens(id),
    workflow VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,  -- Full CitizenCase JSON
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE case_timeline (
    event_id UUID PRIMARY KEY,
    case_id UUID REFERENCES cases(case_id),
    timestamp TIMESTAMP DEFAULT NOW(),
    event_type VARCHAR(50),
    actor VARCHAR(50),
    description TEXT,
    details JSONB
);

CREATE TABLE documents (
    doc_id UUID PRIMARY KEY,
    citizen_id UUID REFERENCES citizens(id),
    doc_type VARCHAR(100),
    storage_key VARCHAR(500),
    encrypted BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE TABLE consents (
    consent_id UUID PRIMARY KEY,
    doc_id UUID REFERENCES documents(doc_id),
    citizen_id UUID REFERENCES citizens(id),
    storage_consent BOOLEAN,
    sharing_consent BOOLEAN,
    automation_consent BOOLEAN,
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE TABLE automation_sessions (
    session_id UUID PRIMARY KEY,
    case_id UUID REFERENCES cases(case_id),
    portal_id VARCHAR(100),
    status VARCHAR(50),
    state JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Connection**:

```python
# backend/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL)

async def get_db() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
```

### 6.3 Caching & Rate Limiting

**Redis for**:
- Session state (OpenClaw browser sessions)
- Rate limiting (per-user API limits)
- Caching (scheme data, 24-hour TTL)

```python
# backend/cache.py

class CacheService:
    def __init__(self):
        self.redis = Redis.from_url(os.getenv("REDIS_URL"))

    async def get_schemes(self, cache_key: str) -> list[Scheme] | None:
        cached = await self.redis.get(f"schemes:{cache_key}")
        if cached:
            return json.loads(cached)
        return None

    async def set_schemes(self, cache_key: str, schemes: list[Scheme]):
        await self.redis.setex(
            f"schemes:{cache_key}",
            86400,  # 24 hours
            json.dumps([s.model_dump() for s in schemes])
        )

    async def rate_limit(self, user_id: str, limit: int = 100) -> bool:
        """Check if user exceeded rate limit."""
        key = f"rate_limit:{user_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 3600)  # Reset after 1 hour
        return current <= limit
```

### 6.4 Observability

**Structured Logging**:

```python
# backend/observability.py

import structlog

logger = structlog.get_logger()

logger.info(
    "case_created",
    case_id=case.case_id,
    workflow=case.workflow.name,
    citizen_id=case.citizen_id,
    intent_confidence=case.intent.confidence,
)

logger.info(
    "automation_checkpoint",
    case_id=case.case_id,
    workflow=case.workflow.name,
    checkpoint_type="OTP_REQUIRED",
    portal_id=session.portal_id,
)
```

**Metrics**:

```python
# Prometheus metrics

from prometheus_client import Counter, Histogram

case_created = Counter("case_created_total", "Total cases created", ["workflow"])
automation_latency = Histogram("automation_duration_seconds", "Automation duration", ["portal"])

case_created.labels(workflow="cpgrams").inc()
automation_latency.labels(portal="cpgrams").observe(42.5)
```

### 6.5 Security Audit Checklist

- [ ] All secrets in environment variables (not code)
- [ ] No NEXT_PUBLIC_* vars contain secrets
- [ ] HTTPS enforced in production
- [ ] CORS restricted to production domains
- [ ] Rate limiting on all endpoints
- [ ] Input validation (Pydantic schemas)
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF tokens for state-changing operations
- [ ] OAuth state validation (DigiLocker, API Setu)
- [ ] Document encryption at rest
- [ ] Audit logs for sensitive operations
- [ ] Consent before data sharing
- [ ] No bypass of CAPTCHA/OTP
- [ ] Session timeout (30 minutes)
- [ ] Password/OTP hashing (bcrypt/Argon2)

---

## PART 7: TESTING STRATEGY

### 7.1 Unit Tests

**Coverage Target**: 80%+

**Priority Tests**:

```python
# tests/test_intent_router.py
def test_rti_intent_detection():
    router = UnifiedIntentRouter()
    result = router.route("I want budget records", {})
    assert result.intent == "information_request"
    assert result.workflow == "rti"
    assert result.confidence >= 0.75

def test_cpgrams_intent_detection():
    router = UnifiedIntentRouter()
    result = router.route("My road hasn't been repaired", {})
    assert result.intent == "government_service_grievance"
    assert result.workflow == "cpgrams"

# tests/test_citizen_case_state.py
def test_case_immutability():
    case = CitizenCase(...)
    with pytest.raises(ValidationError):
        case.workflow.status = "completed"  # Should fail (frozen)

def test_case_serialization():
    case = CitizenCase(...)
    json_str = case.model_dump_json()
    restored = CitizenCase.model_validate_json(json_str)
    assert restored == case

# tests/test_scheme_provider_router.py
def test_fallback_to_local_provider():
    router = SchemeProviderRouter()
    # Mock API Setu failure
    with patch.object(APISetuMySchemeProvider, 'is_available', False):
        schemes, source = router.get_schemes({})
        assert source == "local"
        assert len(schemes) == 3  # Local provider has 3 schemes

# tests/test_form_mapper.py
def test_deterministic_mapping():
    case = CitizenCase(...)
    form = FormSchema(...)
    mapper = FormMapper()

    filled = mapper.map(case, form)
    assert filled.fields[0].value == case.profile.name
    assert filled.fields[0].confidence == 1.0
```

### 7.2 Integration Tests

```python
# tests/integration/test_api_setu.py
@pytest.mark.integration
async def test_myscheme_sandbox_api():
    """Test against API Setu sandbox."""
    provider = APISetuMySchemeProvider()
    provider.sandbox_mode = True

    schemes = await provider.get_schemes({"category": "agriculture"})
    assert len(schemes) > 0
    assert all(s.source_type == "live_api" for s in schemes)

# tests/integration/test_digilocker_oauth.py
@pytest.mark.integration
async def test_digilocker_consent_flow():
    """Test DigiLocker OAuth flow in sandbox."""
    provider = DigiLockerProvider()

    # Generate consent URL
    url = provider.get_consent_url(
        callback_url="http://localhost:3000/callback",
        scope=["aadhaar", "pan"]
    )
    assert "digilocker.meripehchaan.gov.in" in url
    assert "client_id" in url
```

### 7.3 E2E Scenario Tests

**9 Required Scenarios** (from transformation prompt):

```python
# tests/e2e/test_scenarios.py

@pytest.mark.e2e
async def test_scenario_1_road_cpgrams():
    """User: 'My municipal road has not been repaired for two years.'"""
    # 1. Submit input
    # 2. Verify intent → CPGRAMS
    # 3. Verify auto-handoff
    # 4. Fill missing details
    # 5. Generate grievance draft
    # 6. User reviews
    # 7. Confirm
    # 8. (Mock) automation → registration ID
    # 9. Verify tracking active

@pytest.mark.e2e
async def test_scenario_2_road_rti():
    """User: 'I want records showing how much was sanctioned for road repair.'"""
    # 1. Submit input
    # 2. Verify intent → RTI
    # 3. Identify authority
    # 4. Extract records requested
    # 5. Verify correct filing channel (Central vs State)
    # 6. Generate RTI draft
    # 7. Preview
    # 8. (Mock) automation
    # 9. Registration ID

@pytest.mark.e2e
async def test_scenario_3_tenant():
    """User: 'My landlord won't return my deposit.'"""
    # Similar flow for tenant workflow

@pytest.mark.e2e
async def test_scenario_4_labour():
    """User: 'My employer hasn't paid salary for three months.'"""
    # Similar flow for labour workflow

@pytest.mark.e2e
async def test_scenario_5_consumer():
    """User: 'Seller refuses to refund my defective phone.'"""
    # Similar flow for consumer workflow

@pytest.mark.e2e
async def test_scenario_6_scheme():
    """User: 'I am a 21-year-old student in Tamil Nadu looking for schemes.'"""
    # Candidate filtering
    # Minimal questions
    # Isolated rule evaluation
    # Source-backed results

@pytest.mark.e2e
async def test_scenario_7_voice():
    """Speak RTI/CPGRAMS example."""
    # Voice → transcript → intent → workflow → same outcome as text

@pytest.mark.e2e
async def test_scenario_8_document():
    """Upload rent agreement."""
    # OCR → document classification → fact extraction → tenant case state

@pytest.mark.e2e
async def test_scenario_9_low_confidence():
    """User: 'Can you help me?'"""
    # No auto-handoff
    # Clarification question instead
```

### 7.4 Browser Automation Tests

```python
# tests/automation/test_openclaw.py

@pytest.mark.automation
async def test_openclaw_state_machine():
    """Test state transitions."""
    session = SessionState("test-session", "cpgrams")

    assert session.status == "started"

    session.status = "waiting_otp"
    assert "POST /api/openclaw/otp" in session.to_dict()["next_actions"]

    session.status = "awaiting_confirmation"
    assert "payload_digest" in session.to_dict()

@pytest.mark.automation
@pytest.mark.slow
async def test_cpgrams_sandbox_automation():
    """Test against CPGRAMS test portal (if available)."""
    # This requires a CPGRAMS sandbox/test environment
    # Mock if not available
    pass
```

---

## PART 8: DEPLOYMENT STRATEGY

### 8.1 Infrastructure

**Recommended Stack**:

| Component | Service | Rationale |
|-----------|---------|-----------|
| **Backend** | Railway | Supports Playwright, long-running processes, Docker |
| **Frontend** | Vercel | Best Next.js hosting, edge functions, global CDN |
| **Database** | Railway PostgreSQL | Integrated with backend, automatic backups |
| **Cache** | Railway Redis | Session state, rate limiting, caching |
| **Storage** | S3/Cloudflare R2 | Document storage, encrypted at rest |
| **Monitoring** | Railway logs + Sentry | Error tracking, performance monitoring |

### 8.2 Environment Variables

**Backend (.env)**:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/lawtrix

# Redis
REDIS_URL=redis://host:6379/0

# API Keys
SARVAM_API_KEY=sk_...
GEMINI_API_KEY=...
MISTRAL_API_KEY=...

# API Setu (when approved)
APISETU_CLIENT_ID=...
APISETU_CLIENT_SECRET=...
APISETU_SANDBOX=false  # true for sandbox, false for production

# DigiLocker (when approved)
DIGILOCKER_CLIENT_ID=...
DIGILOCKER_CLIENT_SECRET=...
DIGILOCKER_REDIRECT_URI=https://lawtrix.app/auth/digilocker/callback

# Storage
S3_BUCKET=lawtrix-documents
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_REGION=ap-south-1

# Security
JWT_SECRET=...
ENCRYPTION_KEY=...

# Features
BROWSER_AUTOMATION_ENABLED=true
VOICE_ENABLED=true
```

**Frontend (.env.production)**:

```bash
# API URL (public, safe to commit)
NEXT_PUBLIC_API_URL=https://api.lawtrix.app
```

### 8.3 Deployment Workflow

**CI/CD Pipeline** (GitHub Actions):

```yaml
# .github/workflows/deploy.yml

name: Deploy LAWTRIX

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r chakravyuha/requirements.txt
      - run: pytest chakravyuha/tests/ -v

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: railwayapp/railway-deploy@v1
        with:
          service: lawtrix-backend
          environment: production

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: vercel/deploy@v1
        with:
          project: lawtrix-frontend
          environment: production
```

### 8.4 Production Checklist

**Pre-Launch**:
- [ ] All tests passing (unit, integration, E2E)
- [ ] Security audit completed
- [ ] Secrets rotated (no dev keys in production)
- [ ] HTTPS enforced
- [ ] CORS configured for production domain
- [ ] Rate limiting enabled
- [ ] Database migrations applied
- [ ] Redis connection verified
- [ ] S3 bucket configured with encryption
- [ ] Monitoring/logging enabled
- [ ] Error tracking (Sentry) configured
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented

**Go-Live**:
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Configure custom domain (lawtrix.app)
- [ ] SSL certificate verified
- [ ] Test production API endpoints
- [ ] Test OAuth flows (DigiLocker)
- [ ] Smoke test critical workflows
- [ ] Monitor error rates for 24 hours

---

## PART 9: PHASED IMPLEMENTATION ROADMAP

### Week 1: Foundation

**Days 1-2**: Architecture Setup
- ✅ Complete audit (DONE)
- ✅ Research government APIs (DONE)
- [ ] Create unified CitizenCase model
- [ ] Implement case persistence (PostgreSQL)
- [ ] Set up Redis for caching

**Days 3-4**: Intent & Orchestration
- [ ] Implement unified intent router
- [ ] Add automatic workflow handoff
- [ ] Update orchestrator to use CitizenCase
- [ ] Unit tests for routing logic

**Days 5-7**: Scheme Enhancement
- [ ] Implement SchemeProvider abstraction
- [ ] Add LocalVerifiedProvider (current 3 schemes)
- [ ] Expand local catalogue to 15-20 verified schemes
- [ ] Register with API Setu (start approval process)
- [ ] Implement APISetuMySchemeProvider (sandbox first)
- [ ] Unit + integration tests

**Deliverable**: CitizenCase model, enhanced scheme system, auto-handoff working

---

### Week 2: Data Integration & Workflows

**Days 8-9**: API Setu Integration
- [ ] Complete API Setu sandbox testing
- [ ] Implement OAuth 2.0 flow
- [ ] Test myScheme API integration
- [ ] Implement caching strategy (24-hour TTL)
- [ ] Fallback logic (API → local)

**Days 10-11**: DigiLocker Integration
- [ ] Implement DigiLocker OAuth consent flow
- [ ] Document provider abstraction
- [ ] Test document retrieval in sandbox
- [ ] UI for "Connect DigiLocker" flow
- [ ] Consent management

**Days 12-14**: Consumer/Tenant/Labour Workflows
- [ ] Implement ConsumerWorkflowHandler
- [ ] Implement TenantWorkflowHandler (state-aware)
- [ ] Implement LabourWorkflowHandler
- [ ] Add workflow routers
- [ ] Draft generation for each workflow
- [ ] Unit tests

**Deliverable**: Live API integration (sandbox), new civic workflows operational

---

### Week 3: Automation & Intelligence

**Days 15-16**: Form-Filling Engine
- [ ] Implement FormSchema model
- [ ] Implement FormMapper (deterministic)
- [ ] Create portal form definitions (CPGRAMS, RTI)
- [ ] Integration with OpenClaw

**Days 17-18**: Automation Enhancement
- [ ] Formalize automation state machine
- [ ] Add API automation adapters
- [ ] Implement action preview system
- [ ] Human checkpoint UI components

**Days 19-21**: Document Intelligence
- [ ] Implement OCR pipeline (Tesseract or cloud)
- [ ] Document classification
- [ ] Fact extraction for common document types
- [ ] Document wallet with encryption
- [ ] Consent management UI

**Deliverable**: Generic form filling, document intelligence, secure wallet

---

### Week 4: Case Tracking & UX

**Days 22-23**: Case Tracking
- [ ] Implement CaseTracker service
- [ ] Timeline event logging
- [ ] Status polling for CPGRAMS/RTI
- [ ] Reminder scheduling (background jobs)
- [ ] "My Cases" dashboard UI

**Days 24-26**: Frontend Redesign
- [ ] Action-first home screen
- [ ] Guided conversation UI
- [ ] Workflow progress indicator
- [ ] Mobile-responsive layouts
- [ ] Accessibility audit

**Days 27-28**: Polish & Testing
- [ ] E2E scenario tests (9 scenarios)
- [ ] User acceptance testing
- [ ] Performance optimization
- [ ] Bug fixes

**Deliverable**: Production-ready UX, case tracking, E2E tests passing

---

### Week 5: Production Hardening

**Days 29-30**: Authentication & Security
- [ ] Implement JWT authentication
- [ ] OTP-based login
- [ ] Protected endpoints
- [ ] Security audit

**Days 31-32**: Observability
- [ ] Structured logging (structlog)
- [ ] Prometheus metrics
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring

**Days 33-35**: Deployment
- [ ] Railway backend setup
- [ ] Vercel frontend deployment
- [ ] PostgreSQL + Redis configuration
- [ ] S3 bucket for documents
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Production smoke tests

**Deliverable**: Production deployment, monitoring active, auth secured

---

### Week 6: Launch & Iteration

**Days 36-38**: Soft Launch
- [ ] Deploy to production
- [ ] Monitor error rates
- [ ] Gather initial user feedback
- [ ] Fix critical bugs

**Days 39-42**: API Setu Production
- [ ] Receive API Setu approval (if ready)
- [ ] Deploy with production credentials
- [ ] Test live myScheme/DigiLocker APIs
- [ ] Monitor rate limits

**Deliverable**: Live production system with real government APIs

---

## PART 10: SUCCESS METRICS

### Technical Metrics

| Metric | Target |
|--------|--------|
| **Test Coverage** | ≥80% |
| **API Latency (p95)** | <2s |
| **Uptime** | ≥99.5% |
| **Error Rate** | <1% |
| **Automation Success Rate** | ≥85% (browser automation) |
| **Voice Transcription Accuracy** | ≥90% |

### Product Metrics

| Metric | Target (Month 1) |
|--------|-----------------|
| **Cases Created** | 1,000+ |
| **Successful Submissions** | 500+ (RTI + CPGRAMS combined) |
| **Scheme Checks** | 2,000+ |
| **Documents Retrieved (DigiLocker)** | 100+ |
| **User Retention (7-day)** | ≥40% |

### Business Metrics

| Metric | Goal |
|--------|------|
| **Time to RTI Filing** | <10 minutes (vs 2+ hours manual) |
| **Time to CPGRAMS Complaint** | <15 minutes (vs 1+ hour manual) |
| **Scheme Discovery Rate** | 3x vs no platform |
| **Document Collection Time** | <2 minutes (vs 1+ day manual) |

---

## PART 11: RISKS & MITIGATION

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **API Setu Approval Delay** | MEDIUM | HIGH | Start with local provider, sandbox testing, expand catalogue manually |
| **Portal Redesigns Break Automation** | HIGH | MEDIUM | Version detection, portal_registry abstraction, graceful degradation |
| **Voice API Costs** | MEDIUM | MEDIUM | Usage limits, fallback to text, monitor spend |
| **OCR Accuracy Issues** | MEDIUM | LOW | Always require user verification, confidence thresholds |
| **Browser Automation Reliability** | MEDIUM | MEDIUM | Retry logic, session resumability, human fallback |

### Legal/Compliance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Terms Violation (API Setu)** | LOW | CRITICAL | Legal review, clear disclaimers, rate limit enforcement |
| **Data Privacy Violation** | LOW | CRITICAL | DPDP Act compliance, explicit consent, encryption, audit logs |
| **Unauthorized Access** | MEDIUM | HIGH | Authentication, authorization, session timeout |
| **Liability for Wrong Advice** | MEDIUM | HIGH | Clear disclaimers, "information not advice", source attribution |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Government Portal Downtime** | HIGH | MEDIUM | Status detection, queue for retry, user notification |
| **Database Failure** | LOW | CRITICAL | Automated backups, read replicas, disaster recovery plan |
| **Scaling Issues** | MEDIUM | MEDIUM | Horizontal scaling (Railway), caching, background jobs |

---

## PART 12: DECISION MATRIX

### Decision 1: Repository Strategy ⚠️ **USER DECISION REQUIRED**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **A: Build in chakravyuha/, deprecate backend/ + frontend/** | Clean, modern stack, all features exist | Lose MSME compliance tool | ✅ **RECOMMENDED** (unless MSME needed) |
| **B: Merge LAWTRIX MSME as workflow in Chakravyuha** | Unified platform, preserve both | Added complexity | If MSME compliance is in scope |
| **C: Keep separate** | No integration risk | Duplicated infra | If truly unrelated products |

**Chosen**: ________________

---

### Decision 2: Frontend ⚠️ **USER DECISION REQUIRED**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **A: Use chakravyuha-ui (Next.js 16) exclusively** | Modern, integrated, less work | Lose LAWTRIX UI components | ✅ **RECOMMENDED** |
| **B: Migrate LAWTRIX components to Next.js** | Preserve both UIs | Significant migration effort | Only if LAWTRIX UI is superior |
| **C: Build new unified frontend** | Custom design | Most time-consuming | Not recommended |

**Chosen**: ________________

---

### Decision 3: Deployment ⚠️ **USER DECISION REQUIRED**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **A: Railway backend + Vercel frontend** | Playwright support, Next.js optimized | Split infrastructure | ✅ **RECOMMENDED** |
| **B: Single Railway monolith** | Simpler, single service | Slower frontend | If cost is critical |
| **C: Vercel serverless** | Simplest | Browser automation won't work | ❌ Not viable |

**Chosen**: ________________

---

### Decision 4: API Integration Timeline ⚠️ **USER DECISION REQUIRED**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **A: Start API Setu registration now, launch with local data** | No delays, fallback ready | Approval may take 2+ weeks | ✅ **RECOMMENDED** |
| **B: Wait for API approval before launch** | Live data from day 1 | Delays launch by 2-4 weeks | If data freshness critical |
| **C: Skip live APIs indefinitely** | Faster launch | Limited scheme coverage | ❌ Not aligned with vision |

**Chosen**: ________________

---

## CONCLUSION

### The Reality

**This is NOT a rebuild** — it's an enhancement project. Chakravyuha already has:
- ✅ RTI workflow
- ✅ CPGRAMS workflow
- ✅ Scheme eligibility (rule-based)
- ✅ Browser automation with proper gates
- ✅ Voice support
- ✅ Legal RAG
- ✅ Multi-LLM router
- ✅ Document generation

### The Task

**4-6 weeks to production**:
1. Unify architecture (CitizenCase abstraction)
2. Integrate live government APIs (myScheme, DigiLocker)
3. Add missing workflows (consumer, tenant, labour)
4. Enhance UX (action-first, guided, accessible)
5. Production harden (auth, persistence, monitoring)
6. Test comprehensively (E2E scenarios)

### The Opportunity

- 🚀 **4,700+ schemes** vs current 3
- 📄 **300M+ documents** via DigiLocker
- 🔗 **8,036 government APIs** via API Setu
- 🆓 **Free API access** for approved use cases
- ✅ **Commercial use permitted**

### Next Steps

1. **User decisions**: Choose options for 4 decision points above
2. **API Setu registration**: Start immediately (1-2 week approval)
3. **Week 1 implementation**: CitizenCase model + scheme enhancement
4. **Parallel development**: Backend (schemes) + Frontend (UX redesign)
5. **Continuous deployment**: Iterative releases, not big-bang

---

**Ready to proceed?**

Please provide decisions for:
- Decision 1: Repository Strategy (A/B/C)
- Decision 2: Frontend (A/B/C)
- Decision 3: Deployment (A/B/C)
- Decision 4: API Integration Timeline (A/B/C)

Then we begin **Week 1 implementation**.
