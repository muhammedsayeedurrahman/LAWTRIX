"""Unit tests for SchemeProvider."""

from __future__ import annotations

import pytest

from chakravyuha.backend.services.scheme_provider import (
    EligibilityCheck,
    EligibilityResult,
    Scheme,
    SchemeCategory,
    SchemeLevel,
    SchemeProvider,
)


class TestSchemeModel:
    """Test Scheme model."""

    def test_create_scheme(self):
        """Test creating a scheme."""
        scheme = Scheme(
            scheme_id="pmay_urban_001",
            name="Pradhan Mantri Awas Yojana - Urban",
            jurisdiction="India",
            level=SchemeLevel.CENTRAL,
            ministry="Ministry of Housing and Urban Affairs",
            category=SchemeCategory.HOUSING,
            benefit="Financial assistance for house construction/purchase",
            eligibility_criteria=[
                {"field": "annual_income", "operator": "<=", "value": 1800000},
                {"field": "first_home", "operator": "==", "value": True},
            ],
            application_url="https://pmaymis.gov.in/",
            official_source="https://mohua.gov.in/pmay-urban",
        )

        assert scheme.scheme_id == "pmay_urban_001"
        assert scheme.level == SchemeLevel.CENTRAL
        assert scheme.category == SchemeCategory.HOUSING
        assert len(scheme.eligibility_criteria) == 2

    def test_scheme_levels(self):
        """Test scheme level enum."""
        levels = [
            SchemeLevel.CENTRAL,
            SchemeLevel.STATE,
            SchemeLevel.DISTRICT,
            SchemeLevel.LOCAL,
        ]

        for level in levels:
            scheme = Scheme(
                scheme_id=f"test_{level.value}",
                name=f"Test {level.value} Scheme",
                jurisdiction="India",
                level=level,
                ministry="Test Ministry",
                category=SchemeCategory.EDUCATION,
                benefit="Test benefit",
                eligibility_criteria=[],
            )
            assert scheme.level == level

    def test_scheme_categories(self):
        """Test scheme category enum."""
        categories = [
            SchemeCategory.EDUCATION,
            SchemeCategory.HEALTH,
            SchemeCategory.HOUSING,
            SchemeCategory.AGRICULTURE,
            SchemeCategory.EMPLOYMENT,
            SchemeCategory.PENSION,
            SchemeCategory.SUBSIDY,
            SchemeCategory.SCHOLARSHIP,
            SchemeCategory.OTHER,
        ]

        for category in categories:
            scheme = Scheme(
                scheme_id=f"test_{category.value}",
                name=f"Test {category.value} Scheme",
                jurisdiction="India",
                level=SchemeLevel.CENTRAL,
                ministry="Test Ministry",
                category=category,
                benefit="Test benefit",
                eligibility_criteria=[],
            )
            assert scheme.category == category


class TestEligibilityCheck:
    """Test eligibility checking."""

    def test_numeric_less_than_equal(self):
        """Test numeric <= comparison."""
        check = EligibilityCheck(
            field="annual_income",
            operator="<=",
            value=500000,
        )

        # Should pass
        assert check.evaluate({"annual_income": 400000}) is True
        assert check.evaluate({"annual_income": 500000}) is True

        # Should fail
        assert check.evaluate({"annual_income": 600000}) is False

    def test_numeric_greater_than_equal(self):
        """Test numeric >= comparison."""
        check = EligibilityCheck(
            field="age",
            operator=">=",
            value=18,
        )

        assert check.evaluate({"age": 25}) is True
        assert check.evaluate({"age": 18}) is True
        assert check.evaluate({"age": 16}) is False

    def test_numeric_range(self):
        """Test numeric range comparison."""
        check = EligibilityCheck(
            field="age",
            operator="range",
            value=[18, 35],
        )

        assert check.evaluate({"age": 25}) is True
        assert check.evaluate({"age": 18}) is True
        assert check.evaluate({"age": 35}) is True
        assert check.evaluate({"age": 16}) is False
        assert check.evaluate({"age": 40}) is False

    def test_equality_check(self):
        """Test equality comparison."""
        check = EligibilityCheck(
            field="social_category",
            operator="==",
            value="OBC",
        )

        assert check.evaluate({"social_category": "OBC"}) is True
        assert check.evaluate({"social_category": "General"}) is False

    def test_in_list_check(self):
        """Test in list comparison."""
        check = EligibilityCheck(
            field="social_category",
            operator="in",
            value=["SC", "ST", "OBC"],
        )

        assert check.evaluate({"social_category": "SC"}) is True
        assert check.evaluate({"social_category": "OBC"}) is True
        assert check.evaluate({"social_category": "General"}) is False

    def test_boolean_check(self):
        """Test boolean comparison."""
        check = EligibilityCheck(
            field="is_bpl",
            operator="==",
            value=True,
        )

        assert check.evaluate({"is_bpl": True}) is True
        assert check.evaluate({"is_bpl": False}) is False

    def test_missing_field_returns_false(self):
        """Test that missing field returns False."""
        check = EligibilityCheck(
            field="annual_income",
            operator="<=",
            value=500000,
        )

        # Field not in profile
        assert check.evaluate({}) is False
        assert check.evaluate({"age": 25}) is False


@pytest.mark.asyncio
class TestSchemeProvider:
    """Test SchemeProvider functionality."""

    async def test_get_all_schemes(self):
        """Test retrieving all schemes."""
        provider = SchemeProvider()

        schemes = await provider.get_all_schemes()

        assert len(schemes) > 0
        assert all(isinstance(s, Scheme) for s in schemes)

    async def test_get_scheme_by_id(self):
        """Test retrieving scheme by ID."""
        provider = SchemeProvider()

        # Get any scheme first
        schemes = await provider.get_all_schemes()
        test_scheme = schemes[0]

        # Retrieve by ID
        retrieved = await provider.get_scheme(test_scheme.scheme_id)

        assert retrieved is not None
        assert retrieved.scheme_id == test_scheme.scheme_id
        assert retrieved.name == test_scheme.name

    async def test_get_nonexistent_scheme(self):
        """Test retrieving non-existent scheme returns None."""
        provider = SchemeProvider()

        scheme = await provider.get_scheme("nonexistent_scheme_id")

        assert scheme is None

    async def test_filter_schemes_by_category(self):
        """Test filtering schemes by category."""
        provider = SchemeProvider()

        # Filter by education
        education_schemes = await provider.filter_schemes(
            category=SchemeCategory.EDUCATION
        )

        assert all(s.category == SchemeCategory.EDUCATION for s in education_schemes)

    async def test_filter_schemes_by_level(self):
        """Test filtering schemes by level."""
        provider = SchemeProvider()

        central_schemes = await provider.filter_schemes(level=SchemeLevel.CENTRAL)

        assert all(s.level == SchemeLevel.CENTRAL for s in central_schemes)

    async def test_filter_schemes_by_jurisdiction(self):
        """Test filtering schemes by jurisdiction."""
        provider = SchemeProvider()

        tn_schemes = await provider.filter_schemes(jurisdiction="Tamil Nadu")

        assert all("Tamil Nadu" in s.jurisdiction for s in tn_schemes)

    async def test_check_eligibility_eligible(self):
        """Test eligibility check for eligible candidate."""
        provider = SchemeProvider()

        # Create test scheme
        scheme = Scheme(
            scheme_id="test_001",
            name="Test Education Scheme",
            jurisdiction="Tamil Nadu",
            level=SchemeLevel.STATE,
            ministry="Education",
            category=SchemeCategory.EDUCATION,
            benefit="Scholarship",
            eligibility_criteria=[
                {"field": "age", "operator": "<=", "value": 25},
                {"field": "annual_income", "operator": "<=", "value": 500000},
                {"field": "social_category", "operator": "in", "value": ["SC", "ST", "OBC"]},
            ],
        )

        # Eligible profile
        profile = {
            "age": 21,
            "annual_income": 400000,
            "social_category": "OBC",
        }

        result = await provider.check_eligibility(scheme, profile)

        assert result.eligible is True
        assert result.confidence >= 0.9
        assert len(result.passed_criteria) == 3
        assert len(result.failed_criteria) == 0

    async def test_check_eligibility_not_eligible(self):
        """Test eligibility check for non-eligible candidate."""
        provider = SchemeProvider()

        scheme = Scheme(
            scheme_id="test_002",
            name="Test Scheme",
            jurisdiction="India",
            level=SchemeLevel.CENTRAL,
            ministry="Test",
            category=SchemeCategory.OTHER,
            benefit="Test",
            eligibility_criteria=[
                {"field": "age", "operator": "<=", "value": 25},
                {"field": "annual_income", "operator": "<=", "value": 300000},
            ],
        )

        # Not eligible - income too high
        profile = {
            "age": 22,
            "annual_income": 500000,  # Too high
        }

        result = await provider.check_eligibility(scheme, profile)

        assert result.eligible is False
        assert len(result.failed_criteria) > 0

    async def test_find_eligible_schemes(self):
        """Test finding all eligible schemes for a profile."""
        provider = SchemeProvider()

        profile = {
            "age": 21,
            "annual_income": 300000,
            "social_category": "SC",
            "state": "Tamil Nadu",
            "occupation": "student",
        }

        eligible_schemes = await provider.find_eligible_schemes(profile)

        assert isinstance(eligible_schemes, list)
        assert all(isinstance(r, EligibilityResult) for r in eligible_schemes)
        assert all(r.eligible for r in eligible_schemes)

    async def test_find_eligible_schemes_sorted_by_confidence(self):
        """Test that eligible schemes are sorted by confidence."""
        provider = SchemeProvider()

        profile = {
            "age": 20,
            "annual_income": 200000,
        }

        eligible_schemes = await provider.find_eligible_schemes(profile)

        if len(eligible_schemes) > 1:
            # Verify sorted by confidence (descending)
            confidences = [r.confidence for r in eligible_schemes]
            assert confidences == sorted(confidences, reverse=True)

    async def test_candidate_filtering(self):
        """Test candidate filtering for targeted eligibility checking."""
        provider = SchemeProvider()

        # Profile of young student
        profile = {
            "age": 18,
            "occupation": "student",
            "state": "Tamil Nadu",
        }

        # Should return education/scholarship schemes primarily
        candidates = await provider.get_candidate_schemes(profile)

        # Should have some education/scholarship schemes
        education_count = sum(
            1 for s in candidates
            if s.category in [SchemeCategory.EDUCATION, SchemeCategory.SCHOLARSHIP]
        )

        assert education_count > 0

    async def test_missing_profile_data_handling(self):
        """Test handling of missing profile data."""
        provider = SchemeProvider()

        scheme = Scheme(
            scheme_id="test_003",
            name="Test Scheme",
            jurisdiction="India",
            level=SchemeLevel.CENTRAL,
            ministry="Test",
            category=SchemeCategory.OTHER,
            benefit="Test",
            eligibility_criteria=[
                {"field": "age", "operator": "<=", "value": 25},
                {"field": "annual_income", "operator": "<=", "value": 500000},
            ],
        )

        # Incomplete profile - missing annual_income
        profile = {
            "age": 22,
        }

        result = await provider.check_eligibility(scheme, profile)

        # Should not be eligible due to missing data
        assert result.eligible is False
        assert "annual_income" in str(result.missing_information)

    async def test_scheme_search_by_name(self):
        """Test searching schemes by name."""
        provider = SchemeProvider()

        # Search for schemes containing "education" or "scholarship"
        results = await provider.search_schemes(query="education")

        assert all(
            "education" in s.name.lower() or
            "education" in s.category.value.lower()
            for s in results
        )

    async def test_get_scheme_by_category_count(self):
        """Test getting scheme count by category."""
        provider = SchemeProvider()

        stats = await provider.get_statistics()

        assert "total_schemes" in stats
        assert "by_category" in stats
        assert "by_level" in stats
        assert stats["total_schemes"] > 0
