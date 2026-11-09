from tests.conftest import register


def setup_two_people(make_client):
    ana, bia = make_client(), make_client()
    register(ana, email="ana@igreja.org")
    register(bia, email="bia@igreja.org", name="Bia")
    folder = ana.post("/api/folders", json={"name": "Células"}).json()
    note = ana.post("/api/documents", json={"folder_id": folder["id"], "content_md": "# Graça"}).json()
    root_note = ana.post("/api/documents", json={"content_md": "# Raiz"}).json()
    return ana, bia, folder, note, root_note


def test_other_person_lists_nothing(make_client):
    _, bia, folder, _, _ = setup_two_people(make_client)
    assert bia.get("/api/folders").json() == {"folders": [], "breadcrumb": []}
    assert bia.get("/api/documents").json() == {"documents": []}
    assert bia.get(f"/api/folders?parent_id={folder['id']}").status_code == 404
    assert bia.get(f"/api/documents?folder_id={folder['id']}").status_code == 404


def test_foreign_note_is_404_for_read_update_delete(make_client):
    ana, bia, _, note, root_note = setup_two_people(make_client)
    for target in (note, root_note):
        url = f"/api/documents/{target['id']}"
        for response in (bia.get(url), bia.patch(url, json={"title": "invadido"}), bia.delete(url)):
            assert response.status_code == 404
            assert response.json()["error"]["code"] == "not_found"
        assert ana.get(url).json()["title"] == target["title"]


def test_foreign_folder_is_404(make_client):
    ana, bia, folder, _, _ = setup_two_people(make_client)
    url = f"/api/folders/{folder['id']}"
    assert bia.patch(url, json={"name": "Outra"}).status_code == 404
    assert bia.delete(url).status_code == 404
    assert bia.post("/api/folders", json={"name": "Filha", "parent_id": folder["id"]}).status_code == 404
    assert bia.post("/api/documents", json={"folder_id": folder["id"]}).status_code == 404
    assert ana.get("/api/folders").json()["folders"][0]["name"] == "Células"


def test_unknown_id_looks_like_foreign_id(client):
    register(client)
    response = client.get("/api/documents/00000000-0000-4000-8000-000000000000")
    assert response.status_code == 404


def test_folder_tree_breadcrumb_and_rules(client):
    register(client)
    parent = client.post("/api/folders", json={"name": "Células"}).json()
    child = client.post("/api/folders", json={"name": "Quarta", "parent_id": parent["id"]}).json()

    listing = client.get(f"/api/folders?parent_id={child['id']}").json()
    assert listing["breadcrumb"] == [{"id": parent["id"], "name": "Células"}, {"id": child["id"], "name": "Quarta"}]

    duplicate = client.post("/api/folders", json={"name": "células"})
    assert duplicate.status_code == 409
    assert client.post("/api/folders", json={"name": "CÉLULAS"}).status_code == 409
    assert client.post("/api/folders", json={"name": "Células", "parent_id": child["id"]}).status_code == 201

    full = client.delete(f"/api/folders/{parent['id']}")
    assert full.status_code == 409
    assert full.json()["error"]["message"] == "Esvazie a pasta antes de apagá-la."

    renamed = client.patch(f"/api/folders/{parent['id']}", json={"name": "  Grupos  "})
    assert renamed.json()["name"] == "Grupos"


def test_folder_depth_limit(client):
    register(client)
    parent_id = None
    for level in range(20):
        response = client.post("/api/folders", json={"name": f"N{level}", "parent_id": parent_id})
        assert response.status_code == 201, level
        parent_id = response.json()["id"]
    assert client.post("/api/folders", json={"name": "N20", "parent_id": parent_id}).status_code == 422


def test_title_rule_and_listing(client):
    register(client)
    from_heading = client.post("/api/documents", json={"title": "  ", "content_md": "```\n# Não\n```\n## Graça\n"}).json()
    assert from_heading["title"] == "Graça"
    untitled = client.post("/api/documents", json={}).json()
    assert untitled["title"] == "Sem título"
    assert untitled["content_md"] == ""
    assert untitled["passages"] == []

    patched = client.patch(f"/api/documents/{untitled['id']}", json={"title": "", "content_md": "# Fé"}).json()
    assert patched["title"] == "Fé"
    assert patched["created_at"] == untitled["created_at"]

    listing = client.get("/api/documents").json()["documents"]
    assert [d["title"] for d in listing] == ["Fé", "Graça"]
    assert "content_md" not in listing[0]

    assert client.patch(f"/api/documents/{untitled['id']}", json={}).status_code == 422
    assert client.delete(f"/api/documents/{untitled['id']}").status_code == 204
    assert client.get(f"/api/documents/{untitled['id']}").status_code == 404
