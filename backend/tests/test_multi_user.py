from datetime import date

from app.models import AppSettings, Category, Notification, PaymentRecord, Subscription, Tag, User


def _set_csrf(client, response):
    csrf = response.cookies.get("subledger_csrf")
    if csrf:
        client.headers["X-CSRF-Token"] = csrf


def _login(client, username: str, password: str):
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    if response.status_code == 200:
        _set_csrf(client, response)
    return response


def _logout(client):
    response = client.post("/api/auth/logout")
    client.headers.pop("X-CSRF-Token", None)
    return response


def _subscription_payload(name: str):
    return {
        "name": name,
        "amount": 25,
        "currency": "CNY",
        "billing_cycle": "monthly",
        "first_payment_date": "2026-07-01",
    }


def test_admin_can_create_reset_and_delete_user(auth_client, db):
    created = auth_client.post("/api/users", json={
        "username": "alice",
        "password": "alice-password-2026",
        "is_admin": False,
    })
    assert created.status_code == 201
    user_id = created.json()["id"]
    assert created.json()["is_admin"] is False
    assert db.query(Category).filter(Category.user_id == user_id).count() > 0
    assert db.query(AppSettings).filter(AppSettings.user_id == user_id).count() == 1

    reset = auth_client.post(
        f"/api/users/{user_id}/reset-password",
        json={"new_password": "alice-new-password-2026"},
    )
    assert reset.status_code == 200

    assert _logout(auth_client).status_code == 200
    assert _login(auth_client, "alice", "alice-password-2026").status_code == 401
    assert _login(auth_client, "alice", "alice-new-password-2026").status_code == 200

    assert _logout(auth_client).status_code == 200
    assert _login(auth_client, "admin", "testpassword").status_code == 200
    deleted = auth_client.delete(f"/api/users/{user_id}")
    assert deleted.status_code == 200
    assert db.query(User).filter(User.id == user_id).first() is None


def test_users_only_see_their_own_subscription_data(auth_client, db):
    admin_sub = auth_client.post("/api/subscriptions", json=_subscription_payload("管理员订阅"))
    assert admin_sub.status_code == 201
    admin_sub_id = admin_sub.json()["id"]

    created = auth_client.post("/api/users", json={
        "username": "bob",
        "password": "bob-password-2026",
        "is_admin": False,
    })
    assert created.status_code == 201
    bob_id = created.json()["id"]

    assert _logout(auth_client).status_code == 200
    login = _login(auth_client, "bob", "bob-password-2026")
    assert login.status_code == 200
    assert login.json()["is_admin"] is False

    listed = auth_client.get("/api/subscriptions")
    assert listed.status_code == 200
    assert listed.json() == []
    assert auth_client.get(f"/api/subscriptions/{admin_sub_id}").status_code == 404
    assert auth_client.get("/api/users").status_code == 403
    assert auth_client.get("/api/backups").status_code == 403

    bob_sub = auth_client.post("/api/subscriptions", json=_subscription_payload("Bob 订阅"))
    assert bob_sub.status_code == 201
    bob_sub_id = bob_sub.json()["id"]
    assert db.query(Subscription).filter(Subscription.id == bob_sub_id).one().user_id == bob_id
    batch = auth_client.post("/api/subscriptions/batch-toggle", json={"ids": [bob_sub_id], "is_active": False})
    assert batch.status_code == 200
    assert batch.json()["updated"] == 1

    assert _logout(auth_client).status_code == 200
    assert _login(auth_client, "admin", "testpassword").status_code == 200
    listed = auth_client.get("/api/subscriptions")
    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()] == ["管理员订阅"]
    assert auth_client.get(f"/api/subscriptions/{bob_sub_id}").status_code == 404


def test_admin_cannot_delete_self(auth_client, db):
    admin_id = db.query(User.id).filter(User.username == "admin").scalar()
    response = auth_client.delete(f"/api/users/{admin_id}")
    assert response.status_code == 400
    assert response.json()["detail"] == "不能删除当前登录用户"


def test_tags_payments_notifications_export_and_settings_are_isolated(auth_client, db):
    created = auth_client.post("/api/users", json={
        "username": "carol",
        "password": "carol-password-2026",
        "is_admin": False,
    })
    assert created.status_code == 201
    carol_id = created.json()["id"]
    admin_id = db.query(User.id).filter(User.username == "admin").scalar()

    admin_category = Category(user_id=admin_id, name="管理员专属分类")
    admin_tag = Tag(user_id=admin_id, name="相同标签")
    admin_sub = Subscription(
        user_id=admin_id, name="管理员专属服务", amount=10, currency="CNY",
        billing_cycle="once", first_payment_date=date(2026, 7, 1),
        auto_renew=False, category=admin_category, tags=[admin_tag],
    )
    carol_category = db.query(Category).filter(Category.user_id == carol_id).first()
    carol_tag = Tag(user_id=carol_id, name="相同标签")
    carol_sub = Subscription(
        user_id=carol_id, name="Carol 专属服务", amount=20, currency="CNY",
        billing_cycle="once", first_payment_date=date(2026, 7, 1),
        auto_renew=False, category=carol_category, tags=[carol_tag],
    )
    db.add_all([admin_sub, carol_sub])
    db.flush()
    db.add_all([
        PaymentRecord(subscription_id=admin_sub.id, amount=10, currency="CNY", payment_date=date(2026, 7, 1)),
        PaymentRecord(subscription_id=carol_sub.id, amount=20, currency="CNY", payment_date=date(2026, 7, 1)),
        Notification(subscription_id=admin_sub.id, message="管理员专属通知", notify_date=date(2026, 7, 1)),
        Notification(subscription_id=carol_sub.id, message="Carol 专属通知", notify_date=date(2026, 7, 1)),
    ])
    db.commit()

    assert _logout(auth_client).status_code == 200
    assert _login(auth_client, "carol", "carol-password-2026").status_code == 200

    tags = auth_client.get("/api/tags")
    assert tags.status_code == 200
    assert [tag["name"] for tag in tags.json()] == ["相同标签"]
    payments = auth_client.get("/api/payments")
    assert payments.status_code == 200
    assert [item["subscription_name"] for item in payments.json()] == ["Carol 专属服务"]
    notifications = auth_client.get("/api/notifications")
    assert notifications.status_code == 200
    assert [item["message"] for item in notifications.json()["items"]] == ["Carol 专属通知"]
    exported = auth_client.get("/api/data/export?format=json")
    assert exported.status_code == 200
    assert [item["name"] for item in exported.json()] == ["Carol 专属服务"]
    assert auth_client.put("/api/settings", json={"preferred_currency": "USD"}).status_code == 200

    assert _logout(auth_client).status_code == 200
    assert _login(auth_client, "admin", "testpassword").status_code == 200
    assert auth_client.get("/api/settings").json()["preferred_currency"] == "CNY"
