"""Database models for DogeAnalyze."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL

Base = declarative_base()


class MarketData(Base):
    """Market data model for storing Dogecoin price information."""
    
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    price_usd = Column(Numeric(20, 8), nullable=False)
    volume_24h = Column(Numeric(20, 2))
    market_cap = Column(Numeric(20, 2))
    price_change_24h = Column(Numeric(10, 4))
    high_24h = Column(Numeric(20, 8))
    low_24h = Column(Numeric(20, 8))
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<MarketData(id={self.id}, price={self.price_usd}, timestamp={self.timestamp})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'price_usd': float(self.price_usd) if self.price_usd else None,
            'volume_24h': float(self.volume_24h) if self.volume_24h else None,
            'market_cap': float(self.market_cap) if self.market_cap else None,
            'price_change_24h': float(self.price_change_24h) if self.price_change_24h else None,
            'high_24h': float(self.high_24h) if self.high_24h else None,
            'low_24h': float(self.low_24h) if self.low_24h else None,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AnalysisResult(Base):
    """Analysis results model for storing predictions."""
    
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)  # '1h', '4h', '24h'
    predicted_price = Column(Numeric(20, 8))
    confidence_score = Column(Integer)  # 0-100
    trend_direction = Column(String(20))  # 'bullish', 'bearish', 'neutral'
    technical_indicators = Column(Text)  # JSON string
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, timeframe={self.timeframe}, confidence={self.confidence_score})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'timeframe': self.timeframe,
            'predicted_price': float(self.predicted_price) if self.predicted_price else None,
            'confidence_score': self.confidence_score,
            'trend_direction': self.trend_direction,
            'technical_indicators': self.technical_indicators,
            'reasoning': self.reasoning,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ScriptStatus(Base):
    """Script status model for tracking service health."""
    
    __tablename__ = 'script_status'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    script_name = Column(String(50), nullable=False, unique=True, index=True)
    last_run = Column(DateTime)
    status = Column(String(20))  # 'running', 'success', 'error'
    message = Column(Text)
    next_run = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScriptStatus(script={self.script_name}, status={self.status})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'script_name': self.script_name,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'status': self.status,
            'message': self.message,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Database engine and session
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get database session."""
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

