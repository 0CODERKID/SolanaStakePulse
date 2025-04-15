import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Get database connection from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///solana_data.db")

# Flag to track if database is available
database_available = False

# Create SQLAlchemy engine and session with error handling
try:
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database_available = True
        print("Database connection successful")
    else:
        print("DATABASE_URL environment variable not set")
except Exception as e:
    print(f"Database connection error: {str(e)}")
    # Create a dummy engine for when database is not available
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)
Base = declarative_base()

class ValidatorInfo(Base):
    """Store validator information for historical analysis."""
    __tablename__ = 'validator_info'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    epoch = Column(Integer)
    node_pubkey = Column(String(64), index=True)
    vote_pubkey = Column(String(64), index=True)
    activated_stake = Column(Float)
    stake_percentage = Column(Float)
    commission = Column(Integer)
    last_vote = Column(Integer)
    root_slot = Column(Integer)
    credits = Column(Integer)
    status = Column(String(20))
    
class NetworkInfo(Base):
    """Store network-wide information for historical analysis."""
    __tablename__ = 'network_info'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    epoch = Column(Integer, index=True)
    slots_in_epoch = Column(Integer)
    slot_index = Column(Integer)
    epoch_progress = Column(Float)
    hours_remaining = Column(Float)
    inflation_total = Column(Float)
    inflation_validator = Column(Float)
    inflation_foundation = Column(Float)
    total_supply = Column(Float)
    circulating_supply = Column(Float)
    staked_supply = Column(Float)
    staking_ratio = Column(Float)
    active_validators = Column(Integer)
    delinquent_validators = Column(Integer)
    current_slot = Column(Integer)
    data_json = Column(Text)  # Storing additional data as JSON

class StakeAccount(Base):
    """Store stake account information."""
    __tablename__ = 'stake_accounts'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    epoch = Column(Integer, index=True)
    pubkey = Column(String(64), index=True)
    balance = Column(Float)
    parsed_data = Column(Text, nullable=True)  # JSON data

def init_db():
    """Initialize database tables."""
    # Only create tables if database is available
    if database_available:
        try:
            Base.metadata.create_all(engine)
            print("Database tables initialized")
        except Exception as e:
            print(f"Error initializing database tables: {str(e)}")

def store_validators_data(validators_df, epoch):
    """
    Store validator data in the database.
    
    Args:
        validators_df (pandas.DataFrame): Processed validator data
        epoch (int): Current epoch number
    """
    # Skip if database is not available or data is empty
    if not database_available or validators_df is None or validators_df.empty:
        return
        
    session = Session()
    try:
        # Convert DataFrame to list of dictionaries
        validators_data = validators_df.to_dict('records')
        
        # Prepare data for bulk insert
        db_records = []
        for validator in validators_data:
            record = ValidatorInfo(
                timestamp=datetime.now(),
                epoch=epoch,
                node_pubkey=validator.get('nodePubkey'),
                vote_pubkey=validator.get('votePubkey'),
                activated_stake=validator.get('activatedStake', 0),
                stake_percentage=validator.get('stakePercentage', 0),
                commission=validator.get('commission', 0),
                last_vote=validator.get('lastVote', 0),
                root_slot=validator.get('rootSlot', 0),
                credits=validator.get('credits', 0),
                status=validator.get('status', 'Unknown')
            )
            db_records.append(record)
        
        # Bulk insert
        session.bulk_save_objects(db_records)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error storing validator data: {str(e)}")
    finally:
        session.close()

def store_network_info(network_data):
    """
    Store network information in the database.
    
    Args:
        network_data (dict): Processed network information
    """
    # Skip if database is not available or data is empty
    if not database_available or network_data is None:
        return
        
    session = Session()
    try:
        # Create a new record
        record = NetworkInfo(
            timestamp=datetime.now(),
            epoch=network_data['epoch']['current'],
            slots_in_epoch=network_data['epoch']['slots_in_epoch'],
            slot_index=network_data['epoch']['slot_index'],
            epoch_progress=network_data['epoch']['progress_percentage'],
            hours_remaining=network_data['epoch']['hours_remaining'],
            inflation_total=network_data['inflation']['total'],
            inflation_validator=network_data['inflation']['validator'],
            inflation_foundation=network_data['inflation']['foundation'],
            total_supply=network_data['supply']['total'],
            circulating_supply=network_data['supply']['circulating'],
            staked_supply=network_data['supply']['staked'],
            staking_ratio=network_data['supply']['staking_ratio'],
            active_validators=network_data['validators']['active'],
            delinquent_validators=network_data['validators']['delinquent'],
            current_slot=network_data['performance']['current_slot'],
            data_json=json.dumps(network_data)
        )
        
        session.add(record)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error storing network data: {str(e)}")
    finally:
        session.close()

def store_stake_accounts(stake_data, epoch):
    """
    Store stake account information in the database.
    
    Args:
        stake_data (dict): Processed stake information
        epoch (int): Current epoch number
    """
    # Skip if database is not available or data is empty
    if not database_available or stake_data is None or not stake_data.get('accounts'):
        return
        
    session = Session()
    try:
        # Prepare data for bulk insert
        db_records = []
        
        for account in stake_data['accounts']:
            record = StakeAccount(
                timestamp=datetime.now(),
                epoch=epoch,
                pubkey=account.get('pubkey'),
                balance=account.get('balance', 0),
                parsed_data=json.dumps(account.get('parsed')) if account.get('parsed') else None
            )
            db_records.append(record)
        
        # Bulk insert
        session.bulk_save_objects(db_records)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error storing stake account data: {str(e)}")
    finally:
        session.close()

def get_latest_validators_data():
    """
    Retrieve the latest validator data from the database.
    
    Returns:
        pandas.DataFrame: Latest validator data or None if no data is available
    """
    # Return None if database is not available
    if not database_available:
        return None
        
    session = Session()
    try:
        # Get the latest epoch
        latest_epoch = session.query(ValidatorInfo.epoch).order_by(ValidatorInfo.timestamp.desc()).first()
        
        if not latest_epoch:
            return None
            
        # Get all validator records for this epoch
        validators = session.query(ValidatorInfo).filter(
            ValidatorInfo.epoch == latest_epoch[0]
        ).all()
        
        if not validators:
            return None
            
        # Convert to DataFrame
        data = []
        for v in validators:
            data.append({
                'nodePubkey': v.node_pubkey,
                'votePubkey': v.vote_pubkey,
                'activatedStake': v.activated_stake,
                'stakePercentage': v.stake_percentage,
                'commission': v.commission,
                'lastVote': v.last_vote,
                'rootSlot': v.root_slot,
                'credits': v.credits,
                'status': v.status
            })
        
        df = pd.DataFrame(data)
        # Add rank based on stake
        if not df.empty:
            df['rank'] = df['activatedStake'].rank(ascending=False, method='min').astype(int)
            
        return df
    except Exception as e:
        print(f"Error retrieving validator data: {str(e)}")
        return None
    finally:
        session.close()

def get_latest_network_info():
    """
    Retrieve the latest network information from the database.
    
    Returns:
        dict: Latest network information or None if no data is available
    """
    # Return None if database is not available
    if not database_available:
        return None
        
    session = Session()
    try:
        # Get the latest network information
        latest_info = session.query(NetworkInfo).order_by(NetworkInfo.timestamp.desc()).first()
        
        if not latest_info:
            return None
            
        # Convert to dict from JSON field
        return json.loads(latest_info.data_json)
    except Exception as e:
        print(f"Error retrieving network info: {str(e)}")
        return None
    finally:
        session.close()

def get_latest_stake_data(limit=1000):
    """
    Retrieve the latest stake account data from the database.
    
    Args:
        limit (int): Maximum number of stake accounts to retrieve
        
    Returns:
        dict: Processed stake information or None if no data is available
    """
    # Return None if database is not available
    if not database_available:
        return None
        
    session = Session()
    try:
        # Get the latest epoch
        latest_epoch = session.query(StakeAccount.epoch).order_by(StakeAccount.timestamp.desc()).first()
        
        if not latest_epoch:
            return None
            
        # Get stake accounts for this epoch
        accounts = session.query(StakeAccount).filter(
            StakeAccount.epoch == latest_epoch[0]
        ).limit(limit).all()
        
        if not accounts:
            return None
            
        # Convert to desired format
        accounts_data = []
        for account in accounts:
            accounts_data.append({
                'pubkey': account.pubkey,
                'balance': account.balance,
                'parsed': json.loads(account.parsed_data) if account.parsed_data else None
            })
            
        # Process stake distribution
        df = pd.DataFrame([(a['balance']) for a in accounts_data], columns=['balance'])
        
        # Define stake size buckets (in SOL)
        buckets = [0, 100, 1000, 10000, 100000, float('inf')]
        labels = ['0-100', '100-1K', '1K-10K', '10K-100K', '100K+']
        
        stake_distribution = {}
        if not df.empty:
            df['stake_size_category'] = pd.cut(df['balance'], buckets, labels=labels, right=False)
            distribution = df.groupby('stake_size_category').agg(
                count=('balance', 'count'),
                total_sol=('balance', 'sum')
            ).reset_index()
            
            stake_distribution = {
                'categories': distribution['stake_size_category'].tolist(),
                'counts': distribution['count'].tolist(),
                'amounts': distribution['total_sol'].tolist()
            }
        else:
            stake_distribution = {
                'categories': [],
                'counts': [],
                'amounts': []
            }
        
        # Total stake information
        total_stake = df['balance'].sum() if not df.empty else 0
        total_stake_accounts = len(df) if not df.empty else 0
        
        return {
            'total_stake': total_stake,
            'total_accounts': total_stake_accounts,
            'distribution': stake_distribution,
            'accounts': accounts_data
        }
    except Exception as e:
        print(f"Error retrieving stake account data: {str(e)}")
        return None
    finally:
        session.close()

def is_data_fresh(max_age_minutes=60):
    """
    Check if the data in the database is fresh (updated within the last hour).
    
    Args:
        max_age_minutes (int): Maximum data age in minutes to be considered fresh
        
    Returns:
        bool: True if data is fresh, False otherwise
    """
    # Always return False if database is not available
    if not database_available:
        return False
        
    session = Session()
    try:
        # Get the latest timestamp from network info
        latest_timestamp = session.query(NetworkInfo.timestamp).order_by(NetworkInfo.timestamp.desc()).first()
        
        if not latest_timestamp:
            return False
            
        # Check if data is fresh
        max_age = datetime.now() - timedelta(minutes=max_age_minutes)
        return latest_timestamp[0] > max_age
    except Exception as e:
        print(f"Error checking data freshness: {str(e)}")
        return False
    finally:
        session.close()

def get_historical_network_data(days=7):
    """
    Retrieve historical network data for trend analysis.
    
    Args:
        days (int): Number of days of historical data to retrieve
        
    Returns:
        pandas.DataFrame: Historical network data
    """
    # Return None if database is not available
    if not database_available:
        return None
        
    session = Session()
    try:
        # Calculate the start date
        start_date = datetime.now() - timedelta(days=days)
        
        # Get daily network information
        records = session.query(NetworkInfo).filter(
            NetworkInfo.timestamp >= start_date
        ).order_by(NetworkInfo.timestamp).all()
        
        if not records:
            return None
            
        # Convert to DataFrame
        data = []
        for record in records:
            data.append({
                'timestamp': record.timestamp,
                'epoch': record.epoch,
                'staking_ratio': record.staking_ratio,
                'active_validators': record.active_validators,
                'delinquent_validators': record.delinquent_validators,
                'total_validators': record.active_validators + record.delinquent_validators,
                'inflation_total': record.inflation_total
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error retrieving historical data: {str(e)}")
        return None
    finally:
        session.close()

# Initialize the database
init_db()