"""Integration tests for LAWTRIX workflows and services.

Tests complete end-to-end flows across:
- RTI workflow (intent → authority → draft)
- CPGRAMS workflow (classification → department → submission)
- Consumer, Tenant, Labour rights workflows
- Scheme eligibility engine with 17 verified schemes
- Workflow orchestration and handoff
- Database persistence
- Provider routing and fallback

Run with: pytest tests/integration/ -v
Coverage target: 80%+
"""
