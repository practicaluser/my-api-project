# test_posts_api.py

# conftest.py에 정의된 Fixture는 별도로 import할 필요가 없습니다.
# pytest가 자동으로 인식하여 테스트 함수에 주입해줍니다.


def test_create_post(test_client):
    """게시물 생성 API 테스트"""
    response = test_client.post(
        "/posts",
        json={"title": "New Test Post", "content": "This is a test content."},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Test Post"
    assert data["content"] == "This is a test content."
    assert "id" in data


def test_read_post(test_client):
    """단일 게시물 조회 API 테스트"""
    # 1. 조회를 위한 게시물을 먼저 생성
    response_create = test_client.post(
        "/posts",
        json={"title": "Readable Post", "content": "Content to be read."},
    )
    assert response_create.status_code == 201
    post_id = response_create.json()["id"]

    # 2. 생성된 게시물을 조회
    response_read = test_client.get(f"/posts/{post_id}")
    assert response_read.status_code == 200
    data = response_read.json()
    assert data["id"] == post_id
    assert data["title"] == "Readable Post"


def test_read_non_existent_post(test_client):
    """존재하지 않는 게시물을 조회했을 때 404 에러가 발생하는지 테스트"""
    response = test_client.get("/posts/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_read_all_posts(test_client):
    """전체 게시물 목록 조회 API 테스트"""
    # 1. 목록 조회를 위해 여러 게시물 생성
    test_client.post("/posts", json={"title": "Post 1", "content": "Content 1"})
    test_client.post("/posts", json={"title": "Post 2", "content": "Content 2"})

    # 2. 전체 목록 조회
    response = test_client.get("/posts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["title"] == "Post 1"
    assert data[1]["title"] == "Post 2"


def test_update_post(test_client):
    """게시물 수정 API 테스트"""
    # 1. 수정을 위한 게시물 생성
    response_create = test_client.post(
        "/posts", json={"title": "Original", "content": "Original"}
    )
    post_id = response_create.json()["id"]

    # 2. 생성된 게시물 수정
    response_update = test_client.put(
        f"/posts/{post_id}",
        json={"title": "Updated", "content": "Updated"},
    )
    assert response_update.status_code == 200
    data = response_update.json()
    assert data["title"] == "Updated"
    assert data["id"] == post_id


def test_delete_post(test_client):
    """게시물 삭제 API 테스트"""
    # 1. 삭제를 위한 게시물 생성
    response_create = test_client.post(
        "/posts", json={"title": "To Delete", "content": "Delete me"}
    )
    post_id = response_create.json()["id"]

    # 2. 생성된 게시물 삭제
    response_delete = test_client.delete(f"/posts/{post_id}")
    assert response_delete.status_code == 204

    # 3. 실제로 삭제되었는지 확인 (404가 나와야 함)
    response_read = test_client.get(f"/posts/{post_id}")
    assert response_read.status_code == 404
