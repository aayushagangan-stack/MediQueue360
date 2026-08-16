from flask_login import UserMixin


class User(UserMixin):

    def __init__(
        self,
        user_id,
        full_name,
        email,
        password,
        phone,
        role,
        status,
        created_at
    ):

        self.id = user_id
        self.full_name = full_name
        self.email = email
        self.password = password
        self.phone = phone
        self.role = role
        self.status = status
        self.created_at = created_at


    def get_id(self):

        return str(self.id)