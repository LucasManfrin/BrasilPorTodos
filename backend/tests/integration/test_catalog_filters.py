import pytest

from .test_auth import signup
from .test_plans import create_plan, published_policy
from .test_policies import draft, headers

pytestmark = pytest.mark.database


def test_public_catalog_filters_use_published_versions_without_leaking_drafts(auth_client):
    user, _ = signup(auth_client)
    proposal = published_policy(auth_client, user)
    draft(auth_client, user)
    plan = create_plan(auth_client, user, [proposal])
    auth_client.post(f"/api/v1/plans/{plan['id']}/publish", headers=headers(user))
    # Editing the next draft's horizon/category must not change public search.
    auth_client.patch(
        f"/api/v1/policies/{proposal['id']}",
        json={"implementation_start": 2040, "implementation_end": 2050, "category": "HEALTH"},
        headers=headers(user),
    )
    for path in ("policies", "plans"):
        match = auth_client.get(
            f"/api/v1/{path}", params={"year": 2027, "author": user["user"]["username"]}
        )
        assert match.status_code == 200
        assert len(match.json()["data"]) == 1
        assert match.json()["pagination"]["total"] == 1
        for filters in ({"year": 2040}, {"author": "nobody"}, {"q": "no-such-title"}):
            assert auth_client.get(f"/api/v1/{path}", params=filters).json()["data"] == []
    assert len(auth_client.get("/api/v1/policies?category=EDUCATION").json()["data"]) == 1
    assert auth_client.get("/api/v1/policies?category=HEALTH").json()["data"] == []
    assert auth_client.get("/api/v1/plans?year=2201").status_code == 422
