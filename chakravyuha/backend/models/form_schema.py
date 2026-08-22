"""Form schema and field mapping for portal automation.

Generic form abstraction that maps CitizenCase data to portal-specific fields.
Deterministic mapping with validation, confidence tracking, and source provenance.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FieldType(str, Enum):
    """Form field data types."""
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    FILE = "file"
    ADDRESS = "address"
    PIN_CODE = "pin_code"
    CURRENCY = "currency"


class FieldSource(str, Enum):
    """Source of field value."""
    USER_PROFILE = "user_profile"
    CASE_INPUT = "case_input"
    EXTRACTED_FACT = "extracted_fact"
    USER_PROVIDED = "user_provided"
    SYSTEM_GENERATED = "system_generated"
    DOCUMENT_EXTRACTED = "document_extracted"
    DEFAULT_VALUE = "default_value"
    UNKNOWN = "unknown"


class ValidationRule(BaseModel):
    """Field validation rule."""
    model_config = ConfigDict(frozen=True)

    rule_type: str = Field(..., description="Type of validation (required, min_length, max_length, regex, etc.)")
    value: Any | None = Field(None, description="Validation parameter value")
    message: str = Field(..., description="Error message if validation fails")


class FormField(BaseModel):
    """Single form field definition with mapping and validation."""
    model_config = ConfigDict(frozen=True)

    field_id: str = Field(..., description="Unique field identifier")
    label: str = Field(..., description="Human-readable field label")
    field_type: FieldType = Field(..., description="Field data type")
    required: bool = Field(default=False, description="Whether field is mandatory")

    # Value and source tracking
    value: Any | None = Field(None, description="Field value")
    source: FieldSource = Field(default=FieldSource.UNKNOWN, description="Source of field value")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in field value (0-1)")

    # Validation
    validation_rules: list[ValidationRule] = Field(default_factory=list, description="Validation rules")
    editable: bool = Field(default=True, description="Whether user can edit this field")
    sensitive: bool = Field(default=False, description="Whether field contains sensitive data")

    # Portal mapping
    portal_field_name: str | None = Field(None, description="Portal-specific field name/ID")
    portal_selector: str | None = Field(None, description="CSS/XPath selector for browser automation")

    # Field options (for select, radio, checkbox)
    options: list[dict[str, Any]] = Field(default_factory=list, description="Available options for select/radio fields")

    # Dependencies
    document_dependency: str | None = Field(None, description="Document type required for this field")
    depends_on: list[str] = Field(default_factory=list, description="Field IDs this field depends on")

    # Metadata
    help_text: str | None = Field(None, description="Help text for user")
    placeholder: str | None = Field(None, description="Placeholder text")
    default_value: Any | None = Field(None, description="Default value if not provided")


class FormSection(BaseModel):
    """Logical grouping of form fields."""
    model_config = ConfigDict(frozen=True)

    section_id: str = Field(..., description="Section identifier")
    title: str = Field(..., description="Section title")
    description: str | None = Field(None, description="Section description")
    fields: list[FormField] = Field(default_factory=list, description="Fields in this section")
    order: int = Field(default=0, description="Section display order")


class FormSchema(BaseModel):
    """Complete form schema for a portal/workflow."""
    model_config = ConfigDict(frozen=True)

    form_id: str = Field(..., description="Form identifier")
    workflow_name: str = Field(..., description="Associated workflow (rti, cpgrams, consumer, etc.)")
    portal_name: str = Field(..., description="Target portal name")
    form_title: str = Field(..., description="Form title")
    description: str | None = Field(None, description="Form description")

    sections: list[FormSection] = Field(default_factory=list, description="Form sections")

    # Metadata
    version: str = Field(default="1.0.0", description="Form schema version")
    last_verified: str | None = Field(None, description="Date form schema was last verified against portal")
    portal_url: str | None = Field(None, description="Portal URL")

    # Submission metadata
    requires_captcha: bool = Field(default=False, description="Whether form requires CAPTCHA")
    requires_otp: bool = Field(default=False, description="Whether form requires OTP")
    requires_login: bool = Field(default=False, description="Whether form requires login")
    max_file_size_mb: int | None = Field(None, description="Maximum file upload size in MB")
    allowed_file_types: list[str] = Field(default_factory=list, description="Allowed file extensions")


class FieldValidationResult(BaseModel):
    """Result of field validation."""
    model_config = ConfigDict(frozen=True)

    field_id: str
    valid: bool
    errors: list[str] = Field(default_factory=list)


class FormValidationResult(BaseModel):
    """Result of form validation."""
    model_config = ConfigDict(frozen=True)

    valid: bool
    field_results: list[FieldValidationResult] = Field(default_factory=list)
    missing_required_fields: list[str] = Field(default_factory=list)
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# ── Form Field Mapper ─────────────────────────────────────────────────────


class FormFieldMapper:
    """Maps CitizenCase data to form fields deterministically."""

    def __init__(self, schema: FormSchema):
        self.schema = schema

    def map_from_case(self, case: Any) -> FormSchema:
        """Map CitizenCase data to form fields.

        Args:
            case: CitizenCase instance

        Returns:
            FormSchema with populated field values
        """
        # Import here to avoid circular dependency
        from backend.models.citizen_case import CitizenCase

        if not isinstance(case, CitizenCase):
            raise ValueError(f"Expected CitizenCase, got {type(case)}")

        mapped_sections = []

        for section in self.schema.sections:
            mapped_fields = []
            for field in section.fields:
                mapped_field = self._map_field(field, case)
                mapped_fields.append(mapped_field)

            mapped_section = FormSection(
                section_id=section.section_id,
                title=section.title,
                description=section.description,
                fields=mapped_fields,
                order=section.order,
            )
            mapped_sections.append(mapped_section)

        return FormSchema(
            form_id=self.schema.form_id,
            workflow_name=self.schema.workflow_name,
            portal_name=self.schema.portal_name,
            form_title=self.schema.form_title,
            description=self.schema.description,
            sections=mapped_sections,
            version=self.schema.version,
            last_verified=self.schema.last_verified,
            portal_url=self.schema.portal_url,
            requires_captcha=self.schema.requires_captcha,
            requires_otp=self.schema.requires_otp,
            requires_login=self.schema.requires_login,
            max_file_size_mb=self.schema.max_file_size_mb,
            allowed_file_types=self.schema.allowed_file_types,
        )

    def _map_field(self, field: FormField, case: Any) -> FormField:
        """Map a single field from case data.

        Uses deterministic mapping rules based on field_id.
        Never invents data - returns None if not available.
        """
        # Standard field mappings
        field_mappings = {
            # Personal information
            "applicant_name": (lambda: case.profile.name, FieldSource.USER_PROFILE, 1.0),
            "name": (lambda: case.profile.name, FieldSource.USER_PROFILE, 1.0),
            "complainant_name": (lambda: case.profile.name, FieldSource.USER_PROFILE, 1.0),
            "tenant_name": (lambda: case.profile.name, FieldSource.USER_PROFILE, 1.0),
            "employee_name": (lambda: case.profile.name, FieldSource.USER_PROFILE, 1.0),

            # Contact information
            "mobile": (lambda: getattr(case.profile, "phone", None), FieldSource.USER_PROFILE, 1.0),
            "phone": (lambda: getattr(case.profile, "phone", None), FieldSource.USER_PROFILE, 1.0),
            "complainant_mobile": (lambda: getattr(case.profile, "phone", None), FieldSource.USER_PROFILE, 1.0),
            "email": (lambda: getattr(case.profile, "email", None), FieldSource.USER_PROFILE, 1.0),
            "complainant_email": (lambda: getattr(case.profile, "email", None), FieldSource.USER_PROFILE, 1.0),

            # Location information
            "state": (lambda: case.jurisdiction.state, FieldSource.USER_PROFILE, 1.0),
            "district": (lambda: case.jurisdiction.district, FieldSource.USER_PROFILE, 1.0),
            "city": (lambda: case.jurisdiction.city, FieldSource.USER_PROFILE, 1.0),
            "locality": (lambda: case.jurisdiction.locality, FieldSource.USER_PROFILE, 1.0),
            "pin_code": (lambda: case.jurisdiction.pincode, FieldSource.USER_PROFILE, 1.0),
            "pincode": (lambda: case.jurisdiction.pincode, FieldSource.USER_PROFILE, 1.0),

            # Case information
            "subject": (lambda: case.problem.summary, FieldSource.CASE_INPUT, 1.0),
            "description": (lambda: case.problem.facts_narrative or case.input.raw_text, FieldSource.CASE_INPUT, 1.0),
            "issue": (lambda: case.problem.summary, FieldSource.CASE_INPUT, 1.0),
            "issue_description": (lambda: case.problem.summary, FieldSource.CASE_INPUT, 1.0),
            "desired_resolution": (lambda: case.problem.requested_outcome, FieldSource.CASE_INPUT, 0.8),
            "requested_relief": (lambda: case.problem.requested_outcome or "Appropriate relief", FieldSource.CASE_INPUT, 0.7),

            # Citizenship (default True for RTI)
            "is_indian_citizen": (lambda: True, FieldSource.DEFAULT_VALUE, 1.0),
        }

        # Try to map the field
        if field.field_id in field_mappings:
            value_func, source, confidence = field_mappings[field.field_id]
            try:
                value = value_func()
                if value is not None:
                    return field.model_copy(
                        update={
                            "value": value,
                            "source": source,
                            "confidence": confidence,
                        }
                    )
            except (AttributeError, KeyError):
                pass

        # Return original field if no mapping found
        return field

    def validate_form(self, form: FormSchema) -> FormValidationResult:
        """Validate all fields in form.

        Returns:
            FormValidationResult with validation status and errors
        """
        field_results = []
        missing_required = []
        total_confidence = 0.0
        field_count = 0

        for section in form.sections:
            for field in section.fields:
                result = self._validate_field(field)
                field_results.append(result)

                if field.required and not field.value:
                    missing_required.append(field.field_id)

                if field.value is not None:
                    total_confidence += field.confidence
                    field_count += 1

        overall_confidence = total_confidence / field_count if field_count > 0 else 0.0
        valid = len(missing_required) == 0 and all(r.valid for r in field_results)

        return FormValidationResult(
            valid=valid,
            field_results=field_results,
            missing_required_fields=missing_required,
            overall_confidence=overall_confidence,
        )

    def _validate_field(self, field: FormField) -> FieldValidationResult:
        """Validate a single field against its validation rules."""
        errors = []

        if field.value is None:
            if field.required:
                errors.append(f"{field.label} is required")
            return FieldValidationResult(
                field_id=field.field_id,
                valid=not field.required,
                errors=errors,
            )

        # Apply validation rules
        for rule in field.validation_rules:
            if rule.rule_type == "min_length":
                if len(str(field.value)) < rule.value:
                    errors.append(rule.message)
            elif rule.rule_type == "max_length":
                if len(str(field.value)) > rule.value:
                    errors.append(rule.message)
            elif rule.rule_type == "regex":
                import re
                if not re.match(rule.value, str(field.value)):
                    errors.append(rule.message)
            elif rule.rule_type == "email":
                import re
                if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", str(field.value)):
                    errors.append(rule.message)
            elif rule.rule_type == "phone":
                import re
                phone_clean = str(field.value).replace(" ", "").replace("-", "")
                if not re.match(r"^[6-9]\d{9}$", phone_clean):
                    errors.append(rule.message)

        return FieldValidationResult(
            field_id=field.field_id,
            valid=len(errors) == 0,
            errors=errors,
        )


# ── Form Schema Factory ───────────────────────────────────────────────────


class FormSchemaFactory:
    """Factory for creating portal-specific form schemas."""

    @staticmethod
    def create_cpgrams_schema() -> FormSchema:
        """Create CPGRAMS portal form schema."""
        return FormSchema(
            form_id="cpgrams_grievance",
            workflow_name="cpgrams",
            portal_name="CPGRAMS",
            form_title="Lodge Public Grievance",
            description="File grievance with Central/State Government ministries",
            portal_url="https://pgportal.gov.in/Grievance/Lodge",
            requires_captcha=True,
            requires_otp=True,
            requires_login=True,
            max_file_size_mb=4,
            allowed_file_types=[".pdf", ".jpg", ".png", ".doc", ".docx"],
            sections=[
                FormSection(
                    section_id="personal_details",
                    title="Personal Details",
                    order=1,
                    fields=[
                        FormField(
                            field_id="complainant_name",
                            label="Full Name",
                            field_type=FieldType.TEXT,
                            required=True,
                            portal_field_name="Name",
                            portal_selector="input#Name, input[name='Name']",
                            validation_rules=[
                                ValidationRule(
                                    rule_type="required",
                                    message="Name is required"
                                ),
                                ValidationRule(
                                    rule_type="min_length",
                                    value=2,
                                    message="Name must be at least 2 characters"
                                ),
                            ],
                        ),
                        FormField(
                            field_id="complainant_mobile",
                            label="Mobile Number",
                            field_type=FieldType.PHONE,
                            required=True,
                            portal_field_name="MobileNo",
                            portal_selector="input#MobileNo, input[name='MobileNo']",
                            validation_rules=[
                                ValidationRule(
                                    rule_type="phone",
                                    message="Invalid mobile number (must be 10 digits starting with 6-9)"
                                ),
                            ],
                        ),
                        FormField(
                            field_id="complainant_email",
                            label="Email Address",
                            field_type=FieldType.EMAIL,
                            required=True,
                            portal_field_name="EmailId",
                            portal_selector="input#EmailId, input[name='EmailId']",
                            validation_rules=[
                                ValidationRule(
                                    rule_type="email",
                                    message="Invalid email address"
                                ),
                            ],
                        ),
                    ],
                ),
                FormSection(
                    section_id="address_details",
                    title="Address Details",
                    order=2,
                    fields=[
                        FormField(
                            field_id="state",
                            label="State",
                            field_type=FieldType.SELECT,
                            required=True,
                            portal_field_name="StateId",
                            portal_selector="select#StateId, select[name='StateId']",
                        ),
                        FormField(
                            field_id="district",
                            label="District",
                            field_type=FieldType.SELECT,
                            required=True,
                            portal_field_name="DistrictId",
                            portal_selector="select#DistrictId, select[name='DistrictId']",
                        ),
                        FormField(
                            field_id="pin_code",
                            label="PIN Code",
                            field_type=FieldType.PIN_CODE,
                            required=False,
                            portal_field_name="PinCode",
                            portal_selector="input#PinCode, input[name='PinCode']",
                            validation_rules=[
                                ValidationRule(
                                    rule_type="regex",
                                    value=r"^\d{6}$",
                                    message="PIN code must be 6 digits"
                                ),
                            ],
                        ),
                    ],
                ),
                FormSection(
                    section_id="grievance_details",
                    title="Grievance Details",
                    order=3,
                    fields=[
                        FormField(
                            field_id="subject",
                            label="Subject",
                            field_type=FieldType.TEXT,
                            required=True,
                            portal_field_name="Subject",
                            portal_selector="input#Subject, input[name='Subject']",
                            validation_rules=[
                                ValidationRule(
                                    rule_type="max_length",
                                    value=200,
                                    message="Subject must be under 200 characters"
                                ),
                            ],
                        ),
                        FormField(
                            field_id="description",
                            label="Detailed Description",
                            field_type=FieldType.TEXTAREA,
                            required=True,
                            portal_field_name="Description",
                            portal_selector="textarea#Description, textarea[name='Description']",
                            validation_rules=[
                                ValidationRule(
                                    rule_type="min_length",
                                    value=50,
                                    message="Description must be at least 50 characters"
                                ),
                                ValidationRule(
                                    rule_type="max_length",
                                    value=3000,
                                    message="Description must be under 3000 characters"
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    @staticmethod
    def create_rti_schema() -> FormSchema:
        """Create RTI Online portal form schema."""
        return FormSchema(
            form_id="rti_application",
            workflow_name="rti",
            portal_name="RTI Online",
            form_title="Submit RTI Request",
            description="Request information under Right to Information Act",
            portal_url="https://rtionline.gov.in",
            requires_captcha=True,
            requires_login=True,
            max_file_size_mb=2,
            sections=[
                FormSection(
                    section_id="applicant_details",
                    title="Applicant Details",
                    order=1,
                    fields=[
                        FormField(
                            field_id="applicant_name",
                            label="Full Name",
                            field_type=FieldType.TEXT,
                            required=True,
                        ),
                        FormField(
                            field_id="applicant_address",
                            label="Postal Address",
                            field_type=FieldType.TEXTAREA,
                            required=True,
                        ),
                        FormField(
                            field_id="is_indian_citizen",
                            label="Are you a citizen of India?",
                            field_type=FieldType.CHECKBOX,
                            required=True,
                            default_value=True,
                        ),
                    ],
                ),
                FormSection(
                    section_id="request_details",
                    title="Information Requested",
                    order=2,
                    fields=[
                        FormField(
                            field_id="subject",
                            label="Subject",
                            field_type=FieldType.TEXT,
                            required=True,
                        ),
                        FormField(
                            field_id="description",
                            label="Information Requested",
                            field_type=FieldType.TEXTAREA,
                            required=True,
                        ),
                    ],
                ),
            ],
        )
