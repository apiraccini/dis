"""Data access (Protocol-based interfaces + SQLModel async implementations).

Add a Protocol per domain (e.g. DocumentRepository) and an impl backed by
AsyncSession. Protocols enable mocking in service tests without a live DB.
"""
