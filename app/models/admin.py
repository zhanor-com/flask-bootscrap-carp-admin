# admin.py
from datetime import datetime, date
from decimal import Decimal
import bcrypt
from sqlalchemy.sql.expression import ClauseElement
from app.core.base import Base
from app.core.db import db, get_db
from app.core.admin.login.mixins import AdminMixin
class Admin(AdminMixin, Base):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True, nullable=False, comment="ID")
    group_id = db.Column(db.Integer, nullable=False, server_default="1", comment="Group Id")
    name = db.Column(db.String(20), unique=True, nullable=False, comment="Username")
    nickname = db.Column(db.String(50), nullable=False, comment="Nickname")
    password = db.Column(db.String(128), comment="Password")
    avatar = db.Column(db.String(255), comment="Avatar")
    email = db.Column(db.String(100), nullable=False, comment="Email")
    mobile = db.Column(db.String(11), comment="Mobile Number")
    loginfailure = db.Column(
        db.SmallInteger, nullable=False, comment="Login Failure Count"
    )
    logintime = db.Column(db.DateTime, comment="Login Time")
    loginip = db.Column(db.String(50), comment="Login IP")
    created_at = db.Column(db.DateTime, comment="Creation Time")
    updated_at = db.Column(db.DateTime, comment="Update Time")
    token = db.Column(db.String(100), comment="Session Token")
    status = db.Column(db.Enum("normal", "hidden"), nullable=False, server_default='normal',comment="Status")

    def set_password(self, pw):
        db_session = get_db()
        pwhash = bcrypt.hashpw(pw.encode("utf8"), bcrypt.gensalt())
        self.password = pwhash.decode("utf8")
        db_session.commit()

    def check_password(self, pw):
        if not pw:
            return False
        if self.password is not None:
            try:
                expected_hash = self.password.encode("utf8")
                return bcrypt.checkpw(pw.encode("utf8"), expected_hash)
            except ValueError:
                return False
        else:
            return False

    @classmethod
    def from_dict(cls, data):
        """
        Creates an instance of GeneralConfig from a dictionary.
        This method explicitly filters out keys that do not correspond to the model's columns.
        """

        # List all column names of the model
        valid_keys = {column.name for column in cls.__table__.columns}
        # Filter the dictionary to include only keys that correspond to column names
        filtered_data = {key: value for key, value in data.items() if key in valid_keys}
        return cls(**filtered_data)

    def to_dict(self, fields=None):
        """
        Convert this User instance into a dictionary.

        Args:
        - fields: Optional list of fields to include in the dictionary. If None, includes all fields.

        Returns:
        - A dictionary representation of this User instance.
        """
        # If no specific fields are requested, include all fields.
        if fields is None:
            fields = [column.name for column in self.__table__.columns]

        result_dict = {}
        for field in fields:
            value = getattr(self, field, None)

            # Convert datetime and date objects to string for JSON compatibility.
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            # Convert Decimal to string to prevent precision loss during serialization.
            elif isinstance(value, Decimal):
                value = str(value)

            result_dict[field] = value

        return result_dict

    def initialize_special_fields(self):
        for field_name, field in self.__mapper__.columns.items():
            if isinstance(field.type, (db.Enum)):
                options_method = getattr(self, f"{field_name}_property".upper(), None)
                if options_method and hasattr(options_method(), "members"):
                    setattr(self, field_name, field.type.members)
                elif isinstance(field.type, db.Enum):
                    if isinstance(field.default, ClauseElement):
                        pass
                    else:
                        if field.default is not None and hasattr(field.default, "arg"):
                            setattr(
                                self,
                                field_name,
                                (
                                    field.default.arg
                                    if field.default.arg != "None"
                                    else ""
                                ),
                            )

            elif field.default is not None:
                if isinstance(field.default, ClauseElement):
                    pass
                else:
                    if field.default is not None and hasattr(field.default, "arg"):
                        setattr(
                            self,
                            field_name,
                            field.default.arg if field.default.arg != "None" else "",
                        )
            else:
                setattr(self, field_name, "")
