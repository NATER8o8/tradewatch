
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Numeric, Text, func, JSON, Enum, Boolean
import enum

Base = declarative_base()
Base.__allow_unmapped__ = True

class Chamber(str, enum.Enum):
    house = "house"
    senate = "senate"
    executive = "executive"
    other = "other"

class Owner(str, enum.Enum):
    self = "self"
    spouse = "spouse"
    dependent = "dependent"
    joint = "joint"
    unknown = "unknown"

class TxType(str, enum.Enum):
    buy = "buy"
    sell = "sell"
    exchange = "exchange"
    unknown = "unknown"

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

class Official(Base):
    __tablename__ = "officials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    chamber: Mapped['Chamber'] = mapped_column(Enum(Chamber), index=True)
    role: Mapped[str] = mapped_column(String(200), default="")
    state: Mapped[str] = mapped_column(String(50), default="")
    committees: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    trades = relationship("Trade", back_populates="official")

class Trade(Base):
    __tablename__ = "trades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    official_id: Mapped[int] = mapped_column(ForeignKey("officials.id"), index=True)
    filing_url: Mapped[str] = mapped_column(Text, default="")
    transaction_type: Mapped['TxType'] = mapped_column(Enum(TxType), default=TxType.unknown, index=True)
    owner: Mapped['Owner'] = mapped_column(Enum(Owner), default=Owner.unknown, index=True)
    trade_date: Mapped = mapped_column(Date, index=True, nullable=True)
    reported_date: Mapped = mapped_column(Date, index=True, nullable=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True, default="")
    issuer: Mapped[str] = mapped_column(String(256), index=True, default="")
    amount_min: Mapped = mapped_column(Numeric(18,2), nullable=True)
    amount_max: Mapped = mapped_column(Numeric(18,2), nullable=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    official = relationship("Official", back_populates="trades")

class Brief(Base):
    __tablename__ = "briefs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trades.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64), default="openai")
    content_md: Mapped[str] = mapped_column(Text)
    citations: Mapped = mapped_column(JSON, default=list)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

class Frequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"

class Delivery(str, enum.Enum):
    email = "email"
    webhook = "webhook"
    inapp = "inapp"

class AlertRule(Base):
    __tablename__ = "alert_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    min_alpha: Mapped = mapped_column(Numeric(8,4), nullable=True)
    min_sharpe: Mapped = mapped_column(Numeric(8,4), nullable=True)
    sector_pct_threshold: Mapped = mapped_column(Numeric(8,4), nullable=True)
    window_days: Mapped[int] = mapped_column(Integer, default=30)
    sectors: Mapped[str] = mapped_column(Text, default="")
    frequency: Mapped['Frequency'] = mapped_column(Enum(Frequency), default=Frequency.daily)
    delivery: Mapped['Delivery'] = mapped_column(Enum(Delivery), default=Delivery.email)
    webhook_url: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

class Setting(Base):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

class TradeSource(Base):
    __tablename__ = "trade_sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trades.id"), index=True)
    source: Mapped[str] = mapped_column(String(64), default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    raw_json: Mapped[str] = mapped_column(Text, default="")
    retrieved_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True, default="")
    endpoint: Mapped[str] = mapped_column(Text)
    p256dh: Mapped[str] = mapped_column(Text)
    auth: Mapped[str] = mapped_column(Text)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
