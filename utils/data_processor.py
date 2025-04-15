import pandas as pd
import numpy as np
from datetime import datetime
import json

class DataProcessor:
    """
    Process raw data from the Solana blockchain into a format suitable for visualization.
    """
    
    def __init__(self, validators_info, network_info, stake_accounts):
        """
        Initialize with raw data from the Solana blockchain.
        
        Args:
            validators_info (dict): Raw validators data from Solana RPC
            network_info (dict): Network information including epoch, inflation, etc.
            stake_accounts (list): Information about stake accounts
        """
        self.validators_info = validators_info
        self.network_info = network_info
        self.stake_accounts = stake_accounts
        self.processed_validators = self._process_validators()
        self.processed_network_info = self._process_network_info()
        self.processed_stake_info = self._process_stake_accounts()
    
    def _process_validators(self):
        """
        Process raw validator data into a format suitable for visualization.
        
        Returns:
            pandas.DataFrame: Processed validator data
        """
        # Combine current and delinquent validators
        all_validators = self.validators_info.get('current', []) + self.validators_info.get('delinquent', [])
        
        # Create a list to store processed validator data
        processed_data = []
        
        # Calculate total active stake
        total_active_stake = sum(float(v.get('activatedStake', 0)) / 10**9 for v in all_validators)
        
        for validator in all_validators:
            # Convert activated stake from lamports to SOL
            activated_stake_sol = float(validator.get('activatedStake', 0)) / 10**9
            
            # Calculate stake percentage
            stake_percentage = (activated_stake_sol / total_active_stake) * 100 if total_active_stake > 0 else 0
            
            # Calculate credits/epoch (performance)
            epoch_credits = validator.get('epochCredits', [])
            current_epoch_credits = epoch_credits[-1][1] - epoch_credits[-1][0] if epoch_credits else 0
            
            # Determine status (active or delinquent)
            status = "Active" if validator in self.validators_info.get('current', []) else "Delinquent"
            
            processed_data.append({
                'nodePubkey': validator.get('nodePubkey', 'Unknown'),
                'votePubkey': validator.get('votePubkey', 'Unknown'),
                'activatedStake': activated_stake_sol,
                'stakePercentage': stake_percentage,
                'commission': validator.get('commission', 0),
                'lastVote': validator.get('lastVote', 0),
                'rootSlot': validator.get('rootSlot', 0),
                'credits': current_epoch_credits,
                'status': status
            })
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(processed_data)
        
        # Calculate additional metrics
        if not df.empty:
            # Add rank based on stake
            df['rank'] = df['activatedStake'].rank(ascending=False, method='min').astype(int)
            
            # Calculate APY estimate (simplified model)
            inflation_rate = self.network_info.get('inflation_rate', {}).get('total', 8.0)
            df['estimatedAPY'] = (inflation_rate * (1 - df['commission'] / 100)).round(2)
        
        return df
    
    def _process_network_info(self):
        """
        Process network information into a format suitable for visualization.
        
        Returns:
            dict: Processed network information
        """
        # Extract epoch info
        epoch_info = self.network_info.get('epoch_info', {})
        current_epoch = epoch_info.get('epoch', 0)
        slots_in_epoch = epoch_info.get('slotsInEpoch', 0)
        slot_index = epoch_info.get('slotIndex', 0)
        
        # Calculate epoch progress
        epoch_progress = (slot_index / slots_in_epoch * 100) if slots_in_epoch > 0 else 0
        
        # Calculate epoch time remaining (approximate)
        slots_remaining = slots_in_epoch - slot_index
        seconds_per_slot = 0.4  # Solana's approximate slot time
        time_remaining_seconds = slots_remaining * seconds_per_slot
        hours_remaining = time_remaining_seconds / 3600
        
        # Extract inflation data
        inflation_rate = self.network_info.get('inflation_rate', {})
        
        # Extract supply info
        supply_info = self.network_info.get('supply_info', {})
        total_supply = float(supply_info.get('value', {}).get('total', 0)) / 10**9 if supply_info.get('value') else 0
        circulating_supply = float(supply_info.get('value', {}).get('circulating', 0)) / 10**9 if supply_info.get('value') else 0
        
        # Calculate staking metrics
        validators_df = self.processed_validators
        total_staked = validators_df['activatedStake'].sum() if not validators_df.empty else 0
        staking_ratio = (total_staked / circulating_supply * 100) if circulating_supply > 0 else 0
        
        # Validator statistics
        active_validators = validators_df[validators_df['status'] == 'Active'].shape[0] if not validators_df.empty else 0
        delinquent_validators = validators_df[validators_df['status'] == 'Delinquent'].shape[0] if not validators_df.empty else 0
        
        # Calculate stake concentration metrics
        if not validators_df.empty:
            validators_df_sorted = validators_df.sort_values('activatedStake', ascending=False)
            stake_top10 = validators_df_sorted.head(10)['activatedStake'].sum() / total_staked * 100 if total_staked > 0 else 0
            stake_top20 = validators_df_sorted.head(20)['activatedStake'].sum() / total_staked * 100 if total_staked > 0 else 0
            stake_top50 = validators_df_sorted.head(50)['activatedStake'].sum() / total_staked * 100 if total_staked > 0 else 0
        else:
            stake_top10 = stake_top20 = stake_top50 = 0
        
        # Recent performance data (can be improved with historical data)
        cluster_nodes = self.network_info.get('cluster_nodes', [])
        current_slot = self.network_info.get('slot_info', 0)
        
        return {
            'epoch': {
                'current': current_epoch,
                'slots_in_epoch': slots_in_epoch,
                'slot_index': slot_index,
                'progress_percentage': epoch_progress,
                'hours_remaining': hours_remaining
            },
            'inflation': {
                'total': inflation_rate.get('total', 0),
                'validator': inflation_rate.get('validator', 0),
                'foundation': inflation_rate.get('foundation', 0),
                'epoch': current_epoch
            },
            'supply': {
                'total': total_supply,
                'circulating': circulating_supply,
                'staked': total_staked,
                'staking_ratio': staking_ratio
            },
            'validators': {
                'active': active_validators,
                'delinquent': delinquent_validators,
                'total': active_validators + delinquent_validators
            },
            'concentration': {
                'top10': stake_top10,
                'top20': stake_top20,
                'top50': stake_top50
            },
            'performance': {
                'current_slot': current_slot,
                'node_count': len(cluster_nodes)
            },
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _process_stake_accounts(self):
        """
        Process stake account data for visualization.
        
        Returns:
            dict: Processed stake information
        """
        # Extract stake account data
        stake_accounts_data = []
        
        # Check if stake accounts data exists
        if not self.stake_accounts:
            # Return empty data structure if no stake accounts are available
            return {
                'total_stake': 0,
                'total_accounts': 0,
                'distribution': {
                    'categories': [],
                    'counts': [],
                    'amounts': []
                },
                'accounts': []
            }
        
        # Process stake accounts if they exist
        for account in self.stake_accounts:
            pubkey = account.get('pubkey', 'Unknown')
            account_data = account.get('account', {})
            lamports = account_data.get('lamports', 0)
            sol_balance = lamports / 10**9
            
            # Try to extract parsed data if available
            data = account_data.get('data', {})
            parsed_data = None
            if isinstance(data, dict) and 'parsed' in data:
                parsed_data = data.get('parsed', {}).get('info', {})
            
            # For simplicity, we'll just use the balance here
            stake_accounts_data.append({
                'pubkey': pubkey,
                'balance': sol_balance,
                'parsed': parsed_data
            })
        
        # Calculate stake distribution by size
        df = pd.DataFrame(stake_accounts_data)
        
        # Create distribution data
        if not df.empty:
            # Define stake size buckets (in SOL)
            buckets = [0, 100, 1000, 10000, 100000, float('inf')]
            labels = ['0-100', '100-1K', '1K-10K', '10K-100K', '100K+']
            
            df['stake_size_category'] = pd.cut(df['balance'], buckets, labels=labels, right=False)
            stake_distribution = df.groupby('stake_size_category').agg(
                count=('pubkey', 'count'),
                total_sol=('balance', 'sum')
            ).reset_index()
            
            # Convert to dictionary for plotting
            stake_distribution_dict = {
                'categories': stake_distribution['stake_size_category'].tolist(),
                'counts': stake_distribution['count'].tolist(),
                'amounts': stake_distribution['total_sol'].tolist()
            }
        else:
            stake_distribution_dict = {
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
            'distribution': stake_distribution_dict,
            'accounts': stake_accounts_data[:100]  # Limit to first 100 for UI performance
        }
    
    def get_processed_validators(self):
        """
        Get processed validator data.
        
        Returns:
            pandas.DataFrame: Processed validator information
        """
        return self.processed_validators
    
    def get_processed_network_info(self):
        """
        Get processed network information.
        
        Returns:
            dict: Processed network information
        """
        return self.processed_network_info
    
    def get_processed_stake_info(self):
        """
        Get processed stake information.
        
        Returns:
            dict: Processed stake information
        """
        return self.processed_stake_info
