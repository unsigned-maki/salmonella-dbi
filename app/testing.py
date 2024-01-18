import time
import random
from faker import Faker

class TestBuilder:

    def __init__(self, user_connection, poll_connection, user_controller_class, poll_controller_class) -> None:
        self.fake = Faker()
        self.user_connection = user_connection
        self.poll_connection = poll_connection
        self.user_controller = user_controller_class(self.user_connection)
        self.poll_controller = poll_controller_class(self.poll_connection, self.user_controller)

    def test_bulk_insertion(self, num_users):
        insertion_time = 0

        for _ in range(0, num_users):
            now = time.time()
            self.user_controller.create_user(self.fake.user_name()[:15] + str(random.randint(0, 9999)), pw := self.fake.password(), pw)
            insertion_time += time.time() - now
        
        return insertion_time
    
    def test_bulk_insertion_with_polls(self, num_polls):
        insertion_time = 0
        
        id = self.user_controller.create_user(self.fake.user_name()[:15], pw := self.fake.password(), pw)

        for _ in range(0, num_polls):
            now = time.time()
            self.poll_controller.create_poll(id, [self.fake.word() for _ in range(0, 3)], self.fake.sentence()[:10], self.fake.sentence()[:10])
            insertion_time += time.time() - now

        return insertion_time

    def test_find_all(self):
        now = time.time()
        self.poll_controller.get_all()
        return time.time() - now
    
    def test_find_filter(self):
        self.user_controller.create_user(name := self.fake.user_name()[:15], pw := self.fake.password(), pw)
        now = time.time()
        self.user_controller.get_user(name=name)
        return time.time() - now
    
    def test_find_filter_projection(self):
        id = self.user_controller.create_user(self.fake.user_name()[:15], pw := self.fake.password(), pw)
        now = time.time()
        self.user_controller.get_user_password(id)
        return time.time() - now
    
    def test_filter_project_sort(self):
        name = self.fake.user_name()[:15]
        self.user_controller.create_user(name, pw := self.fake.password(), pw)
        now = time.time()
        self.user_controller.search_users(name[:2])
        return time.time() - now
    
    def test_update(self):
        id = self.user_controller.create_user(self.fake.user_name()[:15], pw := self.fake.password(), pw)
        now = time.time()
        self.user_controller.update_user_password(id, pw, pw)
        return time.time() - now
    
    def test_delete(self):
        id = self.user_controller.create_user(self.fake.user_name()[:15], pw := self.fake.password(), pw)
        now = time.time()
        self.user_controller.delete_user(id)
        return time.time() - now

    def run_all(self, num_users=1000, num_polls=1000):
        return {
            "bulk_insertion": self.test_bulk_insertion(num_users),
            "bulk_insertion_with_polls": self.test_bulk_insertion_with_polls(num_polls),
            "find_all": self.test_find_all(),
            "find_filter": self.test_find_filter(),
            "find_filter_projection": self.test_find_filter_projection(),
            "filter_project_sort": self.test_filter_project_sort(),
            "update": self.test_update(),
            "delete": self.test_delete(),
        }
