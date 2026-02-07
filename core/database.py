from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from core.logger import logger

Base = declarative_base()

class HardwareSnapshot(Base):
    __tablename__ = 'hardware_snapshots'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    cpu_usage = Column(Float)
    ram_usage = Column(Float)
    gpu_usage = Column(Float, nullable=True)
    gpu_temp = Column(Float, nullable=True)
    active_game_id = Column(String, nullable=True)
    session_id = Column(Integer, ForeignKey('game_sessions.id'), nullable=True)

class GameSession(Base):
    __tablename__ = 'game_sessions'
    id = Column(Integer, primary_key=True)
    game_id = Column(String)
    game_title = Column(String)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

class CustomGame(Base):
    __tablename__ = 'custom_games'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    exe_path = Column(String)
    icon_path = Column(String, nullable=True)
    added_date = Column(DateTime, default=datetime.datetime.utcnow)

class Favorite(Base):
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True)
    game_title = Column(String, unique=True)
    
import sys

# Trouver le chemin de l'exécutable ou du script
if getattr(sys, 'frozen', False):
    # Si c'est l'EXE
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si c'est le script Python
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, 'data', 'nexus_core.db')
DATA_FOLDER = os.path.join(BASE_DIR, 'data')

# Création du dossier data s'il n'existe pas
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

try:
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    logger.info(f"Database: Connection established at {DB_PATH}")
except Exception as e:
    logger.error(f"Database: Critical connection error: {e}", exc_info=True)

def get_session():
    return Session()