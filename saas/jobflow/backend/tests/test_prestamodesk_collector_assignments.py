from app.models import TenantMembership, User

from test_prestamodesk_collections import (
    BASE_URL,
    add_collector,
    create_loan,
    create_tenant,
    role_headers,
)


def add_tenant_member(
    db_session,
    *,
    tenant,
    email,
    display_name,
    role="member",
    is_active=True,
):
    user = User(
        email=email,
        display_name=display_name,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.flush()

    db_session.add(
        TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role=role,
        )
    )
    db_session.commit()

    return user


def test_owner_lists_only_active_collectors(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=870,
        slug="collector-options",
    )
    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )

    active = add_collector(
        db_session,
        tenant=tenant,
        email="active.assignment@example.test",
        display_name="Active Collector",
    )
    add_collector(
        db_session,
        tenant=tenant,
        email="inactive.assignment@example.test",
        display_name="Inactive Collector",
        is_active=False,
    )
    add_tenant_member(
        db_session,
        tenant=tenant,
        email="member.assignment@example.test",
        display_name="Ordinary Member",
    )

    response = authenticated_client.get(
        f"{BASE_URL}/collections/collectors",
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "user_id": active.id,
            "email": active.email,
            "display_name": active.display_name,
        }
    ]

    collector_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "collector",
    )
    denied = authenticated_client.get(
        f"{BASE_URL}/collections/collectors",
        headers=collector_headers,
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == (
        "Owner role required"
    )


def test_owner_assigns_reassigns_releases_and_reads_history(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=871,
        slug="collector-assignment-lifecycle",
    )
    _, loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=871,
    )
    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )

    first = add_collector(
        db_session,
        tenant=tenant,
        email="first.assignment@example.test",
        display_name="First Collector",
    )
    second = add_collector(
        db_session,
        tenant=tenant,
        email="second.assignment@example.test",
        display_name="Second Collector",
    )
    db_session.commit()

    assigned = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/assignment"
        ),
        json={"collector_user_id": first.id},
        headers=owner_headers,
    )
    assert assigned.status_code == 200
    assert assigned.json()["collector_user_id"] == first.id
    assert assigned.json()["is_active"] is True

    duplicate = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/assignment"
        ),
        json={"collector_user_id": first.id},
        headers=owner_headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == (
        "Loan is already assigned to this collector"
    )

    reassigned = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/assignment"
        ),
        json={"collector_user_id": second.id},
        headers=owner_headers,
    )
    assert reassigned.status_code == 200
    assert reassigned.json()["collector_user_id"] == second.id
    assert reassigned.json()["is_active"] is True

    history_response = authenticated_client.get(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/assignments"
        ),
        headers=owner_headers,
    )
    assert history_response.status_code == 200

    history = history_response.json()
    assert len(history) == 2
    assert history[0]["collector_user_id"] == second.id
    assert history[0]["is_active"] is True
    assert history[1]["collector_user_id"] == first.id
    assert history[1]["is_active"] is False
    assert history[1]["release_reason"] == "Reassigned"

    released = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/assignment/release"
        ),
        json={"reason": "Cuenta pagada"},
        headers=owner_headers,
    )
    assert released.status_code == 200
    assert released.json()["collector_user_id"] == second.id
    assert released.json()["is_active"] is False
    assert released.json()["release_reason"] == (
        "Cuenta pagada"
    )
    assert released.json()["released_by_user_id"] == (
        authenticated_client.auth_user.id
    )

    missing = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/assignment/release"
        ),
        json={"reason": "Repeated release"},
        headers=owner_headers,
    )
    assert missing.status_code == 404


def test_assignment_rejects_invalid_scope_and_roles(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=872,
        slug="collector-assignment-security",
    )
    _, loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=872,
    )
    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )

    valid_collector = add_collector(
        db_session,
        tenant=tenant,
        email="valid.assignment@example.test",
        display_name="Valid Collector",
    )
    inactive_collector = add_collector(
        db_session,
        tenant=tenant,
        email="inactive.security@example.test",
        display_name="Inactive Security Collector",
        is_active=False,
    )
    member = add_tenant_member(
        db_session,
        tenant=tenant,
        email="member.security@example.test",
        display_name="Security Member",
    )

    other_tenant = create_tenant(
        db_session,
        client_number=873,
        slug="collector-assignment-other",
    )
    _, other_loan, _ = create_loan(
        db_session,
        tenant=other_tenant,
        suffix=873,
    )
    other_collector = add_collector(
        db_session,
        tenant=other_tenant,
        email="other.assignment@example.test",
        display_name="Other Collector",
    )
    db_session.commit()

    for invalid_user_id in (
        inactive_collector.id,
        member.id,
        other_collector.id,
    ):
        response = authenticated_client.post(
            (
                f"{BASE_URL}/collections/loans/"
                f"{loan.id}/assignment"
            ),
            json={
                "collector_user_id": invalid_user_id
            },
            headers=owner_headers,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Active collector not found"
        )

    wrong_loan = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{other_loan.id}/assignment"
        ),
        json={"collector_user_id": valid_collector.id},
        headers=owner_headers,
    )
    assert wrong_loan.status_code == 404

    collector_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "collector",
    )
    denied = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/assignment"
        ),
        json={"collector_user_id": valid_collector.id},
        headers=collector_headers,
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == (
        "Owner role required"
    )


def test_owner_filters_assigned_and_unassigned_portfolio(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=874,
        slug="assignment-portfolio-filters",
    )
    _, assigned_loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=874,
    )
    _, unassigned_loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=875,
    )
    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )
    collector = add_collector(
        db_session,
        tenant=tenant,
        email="portfolio.assignment@example.test",
        display_name="Portfolio Collector",
    )
    db_session.commit()

    assigned = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{assigned_loan.id}/assignment"
        ),
        json={"collector_user_id": collector.id},
        headers=owner_headers,
    )
    assert assigned.status_code == 200

    assigned_response = authenticated_client.get(
        f"{BASE_URL}/collections/portfolio",
        params={
            "as_of": "2026-10-02",
            "assignment_status": "assigned",
        },
        headers=owner_headers,
    )
    assert assigned_response.status_code == 200
    assert {
        item["loan_id"]
        for item in assigned_response.json()
    } == {assigned_loan.id}
    assert (
        assigned_response.json()[0][
            "assigned_collector_display_name"
        ]
        == "Portfolio Collector"
    )

    unassigned_response = authenticated_client.get(
        f"{BASE_URL}/collections/portfolio",
        params={
            "as_of": "2026-10-02",
            "assignment_status": "unassigned",
        },
        headers=owner_headers,
    )
    assert unassigned_response.status_code == 200
    assert {
        item["loan_id"]
        for item in unassigned_response.json()
    } == {unassigned_loan.id}

    invalid = authenticated_client.get(
        f"{BASE_URL}/collections/portfolio",
        params={
            "as_of": "2026-10-02",
            "assignment_status": "invalid",
        },
        headers=owner_headers,
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"] == (
        "Invalid assignment status"
    )


def test_collector_cannot_operate_another_collectors_loan(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=876,
        slug="collector-assignment-enforcement",
    )
    _, loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=876,
    )
    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )
    assigned_collector = add_collector(
        db_session,
        tenant=tenant,
        email="assigned.enforcement@example.test",
        display_name="Assigned Enforcement Collector",
    )
    db_session.commit()

    assigned = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/assignment"
        ),
        json={
            "collector_user_id": assigned_collector.id
        },
        headers=owner_headers,
    )
    assert assigned.status_code == 200

    other_collector_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "collector",
    )

    activity = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/activities"
        ),
        headers=other_collector_headers,
        json={
            "channel": "phone",
            "outcome": "Unauthorized attempt",
            "contacted_at": "2026-10-03T13:00:00Z",
        },
    )
    assert activity.status_code == 403
    assert activity.json()["detail"] == (
        "Loan is not assigned to this collector"
    )

    promise = authenticated_client.post(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/promises"
        ),
        headers=other_collector_headers,
        json={
            "promised_amount": "100.00",
            "due_date": "2026-10-10",
        },
    )
    assert promise.status_code == 403

    listed = authenticated_client.get(
        (
            f"{BASE_URL}/collections/loans/"
            f"{loan.id}/activities"
        ),
        headers=other_collector_headers,
    )
    assert listed.status_code == 403
