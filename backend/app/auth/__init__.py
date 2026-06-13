"""Authentication: a swappable provider interface + a signed-cookie session.

``MockAuthProvider`` (dev) and ``AzureOIDCProvider`` (prod) are selected by the
``AUTH_PROVIDER`` setting, so the build does not depend on Temple IT approval.
"""
