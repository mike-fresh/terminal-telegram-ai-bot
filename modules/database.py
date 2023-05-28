from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from modules.message import OpenAIMessage
Base = declarative_base()


class SystemLog(Base):
    __tablename__ = 'system_log'
    id: int = Column(Integer, primary_key=True)
    message: str = Column(Text)
    from_user: str = Column(String)
    to_user: str = Column(String)
    role: str = Column(String, default='user')
    category: str = Column(String)
    chat_id: str = Column(String, default='')
    token_count: int = Column(Integer, default=0)
    date_time: datetime = Column(DateTime, default=datetime.now())


class Message(Base):
    __tablename__ = 'messages'
    id: int = Column(Integer, primary_key=True)
    message: str = Column(Text)
    from_user: str = Column(String)
    to_user: str = Column(String)
    role: str = Column(String)
    category: str = Column(String)
    chat_id: str = Column(String)
    token_count: int = Column(Integer, default=0)
    date_time: datetime = Column(DateTime, default=datetime.now())


class Database:
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        Base.metadata.create_all(self.engine)
        session = sessionmaker(bind=self.engine)
        self.session = session()
        self.session.commit()

    def add_message_to_system_log(self, message, from_user, to_user, role, category, chat_id, token_count, date_time):
        system_log = SystemLog(message=message, from_user=from_user, to_user=to_user,
                               role=role, category=category, chat_id=chat_id,
                               token_count=token_count, date_time=date_time)
        self.session.add(system_log)
        self.session.commit()

    def add_message_to_messages(self, message, from_user, to_user, role, category, chat_id, token_count, date_time):
        message_obj = Message(message=message, from_user=from_user, to_user=to_user,
                              role=role, category=category, chat_id=chat_id,
                              token_count=token_count, date_time=date_time)
        self.session.add(message_obj)
        self.session.commit()

    def get_system_log_from_db(self, chat_id: str):
        return self.session.query(SystemLog).filter_by(chat_id=chat_id).all()

    def get_messages_from_db(self, chat_id: str, category: str) -> list:
        return self.session.query(Message).filter_by(chat_id=chat_id, category=category).all()

    def get_conversation_from_db(self, chat_id: str, category: str) -> list[OpenAIMessage]:
        db_messages = self.get_messages_from_db(chat_id, category)
        messages = []
        for db_message in db_messages:
            message_obj = OpenAIMessage(db_message.message, db_message.from_user, db_message.to_user,
                                        db_message.role, db_message.category, db_message.chat_id,
                                        db_message.token_count)
            messages.append(message_obj)
        return messages

    def get_last_messages_from_db(self, chat_id: str, limit: int = 1) -> list:
        return self.session.query(Message).filter_by(chat_id=chat_id).order_by(desc(Message.id)).limit(limit).all()

    def check_config_exists(self, chat_id: str) -> bool:
        return self.session.query(Message).filter_by(chat_id=chat_id, category='config').first() is not None

    def check_conversation_exists(self, chat_id: str) -> bool:
        return self.session.query(Message).filter_by(chat_id=chat_id).first() is not None

    def remove_conversation(self, chat_id: str) -> list:
        if self.check_conversation_exists(chat_id) is False:
            return []
        conversation: list = self.get_messages_from_db(chat_id, 'user')
        self.session.query(Message).filter_by(chat_id=chat_id).delete()
        self.session.commit()
        return conversation

    def remove_last_message(self, chat_id: str) -> None:
        last_message = self.get_last_messages_from_db(chat_id)
        if last_message:
            self.session.query(Message).filter_by(id=last_message[0].id).delete()
            self.session.commit()
            return last_message[0]

    def get_current_token_count(self, chat_id: str) -> int:
        last_2_messages = self.get_last_messages_from_db(chat_id, 2)
        return sum([msg.token_count for msg in last_2_messages])

    def update_message(self, message_id: int, new_message: str):
        message_obj = self.session.query(Message).filter_by(id=message_id).first()
        if message_obj:
            message_obj.message = new_message
            self.session.commit()
