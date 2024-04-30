from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Создаем движок для работы с базой данных
engine = create_engine('sqlite:///example.db')

# Создаем базовый класс модели
Base = declarative_base()

# Определяем модель для таблицы User
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)

# Создаем таблицы в базе данных (если их еще нет)
Base.metadata.create_all(engine)

# Создаем сессию для взаимодействия с базой данных
Session = sessionmaker(bind=engine)
session = Session()

# Добавляем запись в таблицу
new_user = User(name='Alice', age=30)
session.add(new_user)
session.commit()

# Закрываем сессию
session.close()
