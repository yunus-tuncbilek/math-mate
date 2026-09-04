"""Smoke tests: the app boots, public pages render, auth guards protected ones."""


def test_login_page_renders(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_signup_page_renders(client):
    resp = client.get("/signup")
    assert resp.status_code == 200


def test_index_requires_login(client):
    # The dashboard is @login_required, so an anonymous visitor is redirected.
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


def test_signup_then_login_flow(client):
    email = "teacher@example.com"
    password = "s3cret-pass"

    signup = client.post(
        "/signup",
        data={
            "role": "teacher",
            "name": "Test Teacher",
            "email": email,
            "password": password,
        },
        follow_redirects=True,
    )
    assert signup.status_code == 200

    login = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    # Successful login redirects to the dashboard; bad creds re-render the page.
    assert login.status_code in (301, 302)
