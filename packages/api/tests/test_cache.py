"""Catalogue cache: hits, invalidation on admin writes, and failure tolerance."""

import pytest

from app.core import cache


@pytest.fixture()
def catalogue(client, admin_headers):
    cat = client.post("/api/v1/categories", json={"name": "CacheCat", "slug": "cachecat"}, headers=admin_headers).json()
    return client.post("/api/v1/products", json={
        "name": "Cached Product", "base_price": "15.00", "category_id": cat["id"], "tag_ids": [], "is_featured": True
    }, headers=admin_headers).json()


def test_second_read_is_served_from_cache(client, cache_enabled, catalogue):
    first = client.get("/api/v1/products")
    assert first.status_code == 200

    keys = [k for k in cache_enabled.keys("catalog:*") if not k.endswith(":version")]
    assert keys, "expected the listing to be cached"

    second = client.get("/api/v1/products")
    assert second.json() == first.json()


def test_admin_write_invalidates_the_catalogue(client, cache_enabled, admin_headers, catalogue):
    before = client.get("/api/v1/products").json()
    assert before[0]["base_price"] == "15.00"

    client.put(f"/api/v1/products/{catalogue['id']}", json={"base_price": "21.00"}, headers=admin_headers)

    after = client.get("/api/v1/products").json()
    assert after[0]["base_price"] == "21.00", "stale price served after an admin write"


def test_featured_endpoint_is_invalidated_too(client, cache_enabled, admin_headers, catalogue):
    assert len(client.get("/api/v1/products/featured").json()) == 1

    client.patch(f"/api/v1/products/{catalogue['id']}/feature", headers=admin_headers)

    assert client.get("/api/v1/products/featured").json() == []


def test_product_detail_reflects_writes(client, cache_enabled, admin_headers, catalogue):
    assert client.get(f"/api/v1/products/{catalogue['id']}").json()["name"] == "Cached Product"

    client.put(f"/api/v1/products/{catalogue['id']}", json={"name": "Renamed Product"}, headers=admin_headers)

    assert client.get(f"/api/v1/products/{catalogue['id']}").json()["name"] == "Renamed Product"


def test_invalidation_bumps_the_version_rather_than_scanning_keys(cache_enabled):
    """Key scans block Redis; a version bump is O(1) and orphans everything."""
    first_key = cache.build_key(cache.CATALOG_NAMESPACE, "products")
    cache.invalidate()
    second_key = cache.build_key(cache.CATALOG_NAMESPACE, "products")

    assert first_key != second_key
    assert ":v1:" in first_key and ":v2:" in second_key


def test_distinct_filters_get_distinct_keys(client, cache_enabled, catalogue):
    client.get("/api/v1/products", params={"search": "Cached"})
    client.get("/api/v1/products", params={"search": "Nothing"})

    cached = [k for k in cache_enabled.keys("catalog:*") if not k.endswith(":version")]
    assert len(cached) == 2


def test_cache_outage_degrades_to_database_reads(client, cache_enabled, catalogue, monkeypatch):
    """Redis going down must not take the storefront down with it."""
    class BrokenClient:
        def get(self, *args, **kwargs):
            raise ConnectionError("redis is gone")

        def setex(self, *args, **kwargs):
            raise ConnectionError("redis is gone")

        def incr(self, *args, **kwargs):
            raise ConnectionError("redis is gone")

    monkeypatch.setattr(cache, "get_client", lambda: BrokenClient())

    resp = client.get("/api/v1/products")
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "Cached Product"


def test_caching_disabled_is_a_clean_passthrough(client, catalogue):
    """Default suite config has the cache off; endpoints must still work."""
    assert cache.get_client() is None
    assert client.get("/api/v1/products").status_code == 200
