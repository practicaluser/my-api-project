import random
from faker import Faker
from locust import HttpUser, task, between

# 동적 테스트 데이터를 생성하기 위한 Faker 인스턴스
fake = Faker()


class PostUser(HttpUser):
    """
    게시판(Post) API를 사용하는 가상 유저를 정의합니다.
    """

    # 1. 테스트 대상 서버의 주소
    host = "http://127.0.0.1:8000"

    # 2. 가상 유저가 각 작업을 수행한 후 대기할 시간 (1초 ~ 3초 사이)
    #    실제 사용자의 행동 패턴을 모방합니다.
    wait_time = between(0.1, 0.5)

    # 3. 테스트 중에 생성된 게시물의 ID를 저장할 클래스 변수
    post_ids = []

    @task(10)  # 가중치 10: 가장 빈번하게 실행될 작업
    def list_posts(self):
        """전체 게시물 목록을 조회하는 작업"""
        self.client.get("/posts", name="/posts (list all)")

    @task(1)  # 가중치 1: 가장 드물게 실행될 작업
    def create_post(self):
        """새로운 게시물을 생성하는 작업"""
        headers = {"Content-Type": "application/json"}
        post_data = {
            "title": fake.sentence(nb_words=4),
            "content": fake.text(max_nb_chars=200),
        }

        with self.client.post(
            "/posts",
            json=post_data,
            headers=headers,
            name="/posts (create)",
            catch_response=True,
        ) as response:
            # 요청이 성공적으로 처리되었을 경우 (201 Created)
            if response.status_code == 201:
                try:
                    # 응답 JSON에서 새로 생성된 post의 id를 추출하여 리스트에 추가
                    new_post_id = response.json()["id"]
                    self.__class__.post_ids.append(new_post_id)
                    response.success()
                except Exception as e:
                    response.failure(f"Failed to parse JSON or find id: {e}")
            else:
                response.failure(f"Status code was {response.status_code}")

    @task(5)  # 가중치 5: 중간 빈도로 실행될 작업
    def view_post(self):
        """특정 게시물 하나를 조회하는 작업"""
        # 생성된 게시물이 하나도 없으면 이 작업은 실행하지 않음
        if not self.post_ids:
            return

        # 지금까지 생성된 게시물 ID 중 하나를 무작위로 선택
        post_id = random.choice(self.post_ids)

        # Locust 리포트에서 /posts/1, /posts/2 등을 모두 /posts/[id]로 그룹화하기 위해 name 파라미터 사용
        self.client.get(f"/posts/{post_id}", name="/posts/[id] (view one)")
