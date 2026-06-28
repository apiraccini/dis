"""Business logic services (one class per domain, stateless).

The ingestion pipeline orchestrator will live here (services/ingestion.py):
parse → chunk → embed → store, using the Protocol-based services/protocols.py.
Added in the first SDD implementation session.
"""
