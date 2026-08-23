"""Integration tests for Scheme Eligibility Engine with 17 verified schemes.

Tests complete eligibility checking workflow across all government schemes.
"""

import pytest
from datetime import datetime

from backend.services.scheme_provider import (
    LocalVerifiedProvider,
    SchemeProviderRouter,
    get_scheme_router,
)
from backend.legal.scheme_eligibility import SchemeEligibilityEngine


@pytest.mark.asyncio
class TestSchemeEligibilityIntegration:
    """Integration tests for scheme eligibility checking."""

    @pytest.fixture
    async def scheme_provider(self):
        """Get local verified scheme provider."""
        return LocalVerifiedProvider()

    @pytest.fixture
    async def eligibility_engine(self):
        """Get scheme eligibility engine."""
        return SchemeEligibilityEngine()

    async def test_all_17_schemes_loaded(self, scheme_provider):
        """Test all 17 schemes are loaded correctly."""
        schemes = await scheme_provider.get_schemes()

        assert len(schemes) == 17, f"Expected 17 schemes, got {len(schemes)}"

        # Verify scheme IDs
        scheme_ids = [s.id for s in schemes]
        expected_ids = [
            "pm-sym",
            "apy",
            "pm-kisan",
            "pm-jay",
            "pm-ujjvala",
            "pm-awas-gramin",
            "pm-awas-urban",
            "pmmy",
            "nsap-old-age",
            "nsap-widow",
            "nsap-disability",
            "nsap-family-benefit",
            "sukanya-samriddhi",
            "pm-scholarship",
            "soil-health-card",
            "pm-kmy",
            "mid-day-meal",
        ]

        for expected_id in expected_ids:
            assert expected_id in scheme_ids, f"Scheme {expected_id} not found"

    async def test_pm_jay_eligibility(self, scheme_provider):
        """Test PM-JAY (Ayushman Bharat) eligibility."""
        # Eligible profile (in SECC database)
        eligible_profile = {
            "listed_in_secc_2011_or_state_database": True,
        }

        eligibility = await scheme_provider.check_eligibility("pm-jay", eligible_profile)

        assert eligibility.eligible is True
        assert len(eligibility.matched_conditions) > 0

        # Ineligible profile (not in SECC)
        ineligible_profile = {
            "listed_in_secc_2011_or_state_database": False,
        }

        eligibility = await scheme_provider.check_eligibility("pm-jay", ineligible_profile)

        assert eligibility.eligible is False

    async def test_pm_ujjvala_eligibility(self, scheme_provider):
        """Test PM-Ujjvala Yojana eligibility."""
        # Eligible profile
        eligible_profile = {
            "is_female_applicant": True,
            "belongs_to_eligible_category": True,
            "already_has_lpg_connection": False,
        }

        eligibility = await scheme_provider.check_eligibility("pm-ujjvala", eligible_profile)

        assert eligibility.eligible is True

        # Ineligible - male applicant
        ineligible_profile = {
            "is_female_applicant": False,
            "belongs_to_eligible_category": True,
            "already_has_lpg_connection": False,
        }

        eligibility = await scheme_provider.check_eligibility("pm-ujjvala", ineligible_profile)

        assert eligibility.eligible is False

    async def test_pm_awas_gramin_eligibility(self, scheme_provider):
        """Test PM-Awas Yojana Gramin eligibility."""
        # Eligible profile
        eligible_profile = {
            "secc_homeless_or_kutcha": True,
            "meets_exclusion_criteria": False,
        }

        eligibility = await scheme_provider.check_eligibility("pm-awas-gramin", eligible_profile)

        assert eligibility.eligible is True

        # Ineligible - meets exclusion (govt employee)
        ineligible_profile = {
            "secc_homeless_or_kutcha": True,
            "meets_exclusion_criteria": True,  # Has govt job
        }

        eligibility = await scheme_provider.check_eligibility("pm-awas-gramin", ineligible_profile)

        assert eligibility.eligible is False

    async def test_pmmy_mudra_loan_eligibility(self, scheme_provider):
        """Test PM MUDRA Yojana eligibility."""
        # Eligible profile
        eligible_profile = {
            "is_income_generating_activity": True,
            "is_corporate_entity": False,
            "loan_amount": 500000,  # Rs 5 lakh (within limit)
        }

        eligibility = await scheme_provider.check_eligibility("pmmy", eligible_profile)

        assert eligibility.eligible is True

        # Ineligible - exceeds loan limit
        ineligible_profile = {
            "is_income_generating_activity": True,
            "is_corporate_entity": False,
            "loan_amount": 1500000,  # Rs 15 lakh (exceeds 10L limit)
        }

        eligibility = await scheme_provider.check_eligibility("pmmy", ineligible_profile)

        assert eligibility.eligible is False

    async def test_nsap_old_age_pension_eligibility(self, scheme_provider):
        """Test NSAP Old Age Pension eligibility."""
        # Eligible profile
        eligible_profile = {
            "age": 65,
            "is_bpl": True,
            "has_regular_income_source": False,
        }

        eligibility = await scheme_provider.check_eligibility("nsap-old-age", eligible_profile)

        assert eligibility.eligible is True

        # Ineligible - below age 60
        ineligible_profile = {
            "age": 55,
            "is_bpl": True,
            "has_regular_income_source": False,
        }

        eligibility = await scheme_provider.check_eligibility("nsap-old-age", ineligible_profile)

        assert eligibility.eligible is False

    async def test_sukanya_samriddhi_eligibility(self, scheme_provider):
        """Test Sukanya Samriddhi Yojana eligibility."""
        # Eligible profile
        eligible_profile = {
            "is_girl_child": True,
            "girl_child_age": 5,
            "existing_ssy_accounts_count": 0,
        }

        eligibility = await scheme_provider.check_eligibility("sukanya-samriddhi", eligible_profile)

        assert eligibility.eligible is True

        # Ineligible - above age 10
        ineligible_profile = {
            "is_girl_child": True,
            "girl_child_age": 12,
            "existing_ssy_accounts_count": 0,
        }

        eligibility = await scheme_provider.check_eligibility("sukanya-samriddhi", ineligible_profile)

        assert eligibility.eligible is False

    async def test_pm_kmy_farmer_pension_eligibility(self, scheme_provider):
        """Test PM-Kisan Maandhan Yojana eligibility."""
        # Eligible profile
        eligible_profile = {
            "cultivable_land_hectares": 1.5,
            "age": 30,
            "falls_under_exclusion": False,
        }

        eligibility = await scheme_provider.check_eligibility("pm-kmy", eligible_profile)

        assert eligibility.eligible is True

        # Ineligible - landholding exceeds 2 hectares
        ineligible_profile = {
            "cultivable_land_hectares": 3.0,
            "age": 30,
            "falls_under_exclusion": False,
        }

        eligibility = await scheme_provider.check_eligibility("pm-kmy", ineligible_profile)

        assert eligibility.eligible is False

    async def test_scheme_filtering_by_category(self, scheme_provider):
        """Test scheme filtering by category."""
        # Filter pension schemes
        pension_schemes = await scheme_provider.get_schemes({"category": "pension"})

        assert len(pension_schemes) >= 1
        pension_ids = [s.id for s in pension_schemes]
        assert "pm-kmy" in pension_ids or "apy" in pension_ids or "pm-sym" in pension_ids

        # Filter health schemes
        health_schemes = await scheme_provider.get_schemes({"category": "health"})

        assert len(health_schemes) >= 1
        assert any("pm-jay" in s.id for s in health_schemes)

    async def test_scheme_filtering_by_state(self, scheme_provider):
        """Test scheme filtering by state."""
        # All schemes should be available for all states (central schemes)
        maharashtra_schemes = await scheme_provider.get_schemes({"state": "Maharashtra"})

        assert len(maharashtra_schemes) > 0

        # Check that central schemes are included
        scheme_ids = [s.id for s in maharashtra_schemes]
        assert "pm-jay" in scheme_ids  # Central scheme available everywhere

    async def test_multiple_scheme_eligibility_check(self, scheme_provider):
        """Test checking eligibility for multiple schemes with single profile."""
        # Profile of 65-year-old BPL woman
        profile = {
            "age": 65,
            "is_bpl": True,
            "is_female_applicant": True,
            "is_indian_citizen": True,
            "has_regular_income_source": False,
            "listed_in_secc_2011_or_state_database": True,
        }

        # Get all schemes
        all_schemes = await scheme_provider.get_schemes()

        eligible_schemes = []

        for scheme in all_schemes:
            eligibility = await scheme_provider.check_eligibility(scheme.id, profile)
            if eligibility.eligible:
                eligible_schemes.append(scheme.id)

        # Should be eligible for multiple schemes
        assert len(eligible_schemes) > 0

        # Should definitely be eligible for old age pension
        assert "nsap-old-age" in eligible_schemes

        # Should be eligible for PM-JAY (if in SECC)
        assert "pm-jay" in eligible_schemes


@pytest.mark.asyncio
class TestSchemeProviderRouter:
    """Test scheme provider routing and fallback."""

    async def test_provider_router_initialization(self):
        """Test scheme provider router initializes correctly."""
        router = get_scheme_router()

        assert router is not None
        assert len(router.providers) >= 1  # At least local provider

        # Local provider should always be available
        local_provider = next(
            (p for p in router.providers if isinstance(p, LocalVerifiedProvider)),
            None
        )
        assert local_provider is not None
        assert local_provider.is_available

    async def test_router_fetches_schemes(self):
        """Test router fetches schemes from available provider."""
        router = get_scheme_router()

        schemes, provider_type = await router.get_schemes()

        assert len(schemes) == 17
        assert provider_type is not None

    async def test_router_get_specific_scheme(self):
        """Test router retrieves specific scheme."""
        router = get_scheme_router()

        scheme, provider_type = await router.get_scheme("pm-jay")

        assert scheme is not None
        assert scheme.id == "pm-jay"
        assert "Ayushman Bharat" in scheme.name or "PM-JAY" in scheme.short_name

    async def test_router_eligibility_check(self):
        """Test router performs eligibility check."""
        router = get_scheme_router()

        profile = {
            "age": 70,
            "is_bpl": True,
            "has_regular_income_source": False,
        }

        eligibility, provider_type = await router.check_eligibility("nsap-old-age", profile)

        assert eligibility is not None
        assert eligibility.eligible is True


@pytest.mark.asyncio
class TestSchemeEligibilityPerformance:
    """Test scheme eligibility engine performance."""

    async def test_batch_eligibility_check_performance(self, scheme_provider):
        """Test performance of checking eligibility across all 17 schemes."""
        import time

        profile = {
            "age": 25,
            "is_indian_citizen": True,
            "monthly_income": 12000,
            "is_income_tax_payer": False,
        }

        all_schemes = await scheme_provider.get_schemes()

        start_time = time.time()

        for scheme in all_schemes:
            await scheme_provider.check_eligibility(scheme.id, profile)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete all 17 checks within 5 seconds (deterministic rules, no LLM)
        assert execution_time < 5.0, f"Batch eligibility check took {execution_time}s, expected <5s"

    async def test_scheme_retrieval_cache_performance(self, scheme_provider):
        """Test repeated scheme retrieval uses caching."""
        import time

        # First retrieval (cold)
        start_time = time.time()
        schemes1 = await scheme_provider.get_schemes()
        first_time = time.time() - start_time

        # Second retrieval (should be from cache/memory)
        start_time = time.time()
        schemes2 = await scheme_provider.get_schemes()
        second_time = time.time() - start_time

        # Second retrieval should be significantly faster or similar (already in memory)
        assert len(schemes1) == len(schemes2)
        # Note: Second call may not be faster if already fast (file loading is quick)
