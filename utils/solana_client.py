import json
import requests
import base64
import os
import time
from datetime import datetime

# Import database functions
from utils.database import (init_db, store_validators_data, store_network_info, store_stake_accounts,
                          get_latest_validators_data, get_latest_network_info, get_latest_stake_data,
                          is_data_fresh)

class SolanaClient:
    """
    Client for interacting with the Solana blockchain to fetch staking-related data.
    """
    
    def __init__(self, rpc_endpoint="https://api.mainnet-beta.solana.com"):
        """
        Initialize the Solana client with the given RPC endpoint.
        
        Args:
            rpc_endpoint (str): URL of the Solana RPC endpoint
        """
        self.rpc_endpoint = rpc_endpoint
    
    def _make_rpc_request(self, method, params=None):
        """
        Make a direct RPC request to the Solana endpoint.
        
        Args:
            method (str): The RPC method to call
            params (list, optional): Parameters for the RPC call
            
        Returns:
            dict: The JSON response from the RPC endpoint
        """
        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        
        response = requests.post(self.rpc_endpoint, headers=headers, json=data)
        
        if response.status_code != 200:
            raise Exception(f"RPC request failed with status {response.status_code}: {response.text}")
        
        result = response.json()
        
        if "error" in result:
            raise Exception(f"RPC error: {result['error']}")
        
        return result["result"]
    
    def get_validators(self, use_cache=True, cache_max_age=30):
        """
        Fetch all validators data from the Solana network or database cache.
        
        Args:
            use_cache (bool): Whether to use cached data if available
            cache_max_age (int): Maximum age in minutes for cache to be considered fresh
            
        Returns:
            dict: Information about all validators in the network
        """
        # Check if we can use cached data
        if use_cache:
            # Try to get data from database
            cached_data = get_latest_validators_data()
            if cached_data is not None:
                # Return as a dict compatible with direct RPC response
                return {
                    "current": cached_data[cached_data["status"] == "current"].to_dict("records"),
                    "delinquent": cached_data[cached_data["status"] == "delinquent"].to_dict("records")
                }
        
        # If no cached data or cache is stale, fetch from RPC
        data = self._make_rpc_request("getVoteAccounts")
        return data
    
    def get_epoch_info(self):
        """
        Get information about the current epoch.
        
        Returns:
            dict: Current epoch information
        """
        return self._make_rpc_request("getEpochInfo")
    
    def get_inflation_rate(self):
        """
        Get the current inflation rate.
        
        Returns:
            dict: Information about the current inflation rate
        """
        return self._make_rpc_request("getInflationRate")
    
    def get_supply(self):
        """
        Get information about the current supply of SOL.
        
        Returns:
            dict: Information about the total and circulating supply
        """
        return self._make_rpc_request("getSupply")
    
    def get_network_info(self, use_cache=True, cache_max_age=30):
        """
        Get comprehensive information about the Solana network.
        
        Args:
            use_cache (bool): Whether to use cached data if available
            cache_max_age (int): Maximum age in minutes for cache to be considered fresh
            
        Returns:
            dict: Combined network information including epoch, inflation, and supply data
        """
        # Check if we can use cached data
        if use_cache:
            # Try to get data from database
            cached_data = get_latest_network_info()
            if cached_data is not None:
                return cached_data
        
        # If no cached data or cache is stale, fetch from RPC
        try:
            epoch_info = self.get_epoch_info()
            inflation_rate = self.get_inflation_rate()
            supply_info = self.get_supply()
            slot_info = self._make_rpc_request("getSlot")
            
            # Get cluster nodes for geo-distribution
            cluster_nodes = self._make_rpc_request("getClusterNodes")
            
            # Process the data for dashboard consumption
            current_epoch = epoch_info.get("epoch", 0)
            slots_in_epoch = epoch_info.get("slotsInEpoch", 0)
            slot_index = epoch_info.get("slotIndex", 0)
            
            # Calculate progress and time remaining
            epoch_progress = (slot_index / slots_in_epoch * 100) if slots_in_epoch > 0 else 0
            slots_remaining = slots_in_epoch - slot_index
            # Assuming avg 2 seconds per slot
            hours_remaining = slots_remaining * 2 / 3600
            
            # Process validator counts
            validators = self.get_validators(use_cache=use_cache)
            current_validators = len(validators.get("current", []))
            delinquent_validators = len(validators.get("delinquent", []))
            
            # Process inflation data
            total_inflation = inflation_rate.get("total", 0) * 100  # Convert to percentage
            validator_inflation = inflation_rate.get("validator", 0) * 100
            foundation_inflation = inflation_rate.get("foundation", 0) * 100
            
            # Process supply data
            total_supply = float(supply_info.get("value", {}).get("total", 0)) / 1e9  # Convert lamports to SOL
            circulating_supply = float(supply_info.get("value", {}).get("circulating", 0)) / 1e9
            
            # Calculate staked supply (from validators)
            total_stake = 0
            for validator in validators.get("current", []) + validators.get("delinquent", []):
                total_stake += float(validator.get("activatedStake", 0)) / 1e9
                
            staking_ratio = total_stake / total_supply if total_supply > 0 else 0
            
            processed_data = {
                "epoch": {
                    "current": current_epoch,
                    "slots_in_epoch": slots_in_epoch,
                    "slot_index": slot_index,
                    "progress_percentage": epoch_progress,
                    "hours_remaining": hours_remaining
                },
                "inflation": {
                    "total": total_inflation,
                    "validator": validator_inflation,
                    "foundation": foundation_inflation
                },
                "supply": {
                    "total": total_supply,
                    "circulating": circulating_supply,
                    "staked": total_stake,
                    "staking_ratio": staking_ratio
                },
                "validators": {
                    "active": current_validators,
                    "delinquent": delinquent_validators 
                },
                "performance": {
                    "current_slot": slot_info
                },
                "raw_data": {
                    "epoch_info": epoch_info,
                    "inflation_rate": inflation_rate,
                    "supply_info": supply_info,
                    "cluster_nodes": cluster_nodes
                }
            }
            
            # Store in the database for future use
            try:
                store_network_info(processed_data)
            except Exception as e:
                print(f"Warning: Failed to store network info in database: {str(e)}")
                
            return processed_data
        except Exception as e:
            raise Exception(f"Failed to get network info: {str(e)}")
    
    def get_stake_accounts(self, use_cache=True, cache_max_age=30, limit=50):
        """
        Get stake accounts from the network or database cache.
        
        Args:
            use_cache (bool): Whether to use cached data if available
            cache_max_age (int): Maximum age in minutes for cache to be considered fresh
            limit (int): Maximum number of accounts to fetch
            
        Returns:
            list: Information about stake accounts
        """
        # Check if we can use cached data
        if use_cache:
            # Try to get data from database
            cached_data = get_latest_stake_data(limit=limit)
            if cached_data is not None:
                # Convert to format expected by the data processor
                processed_accounts = []
                for account in cached_data.get('accounts', []):
                    processed_accounts.append({
                        'pubkey': account['pubkey'],
                        'account': {
                            'lamports': int(account['balance'] * 1e9),  # Convert back to lamports
                            'data': {
                                'parsed': account['parsed'] if account['parsed'] else {}
                            }
                        }
                    })
                return processed_accounts
        
        # If no cached data or cache is stale, fetch from RPC
        try:
            # Program ID for the Stake program
            stake_program_id = "Stake11111111111111111111111111111111111111"
            
            # Use getProgramAccounts to get all stake accounts but with a reduced limit
            # to avoid RPC errors with "accumulated scan results exceeded the limit"
            params = [
                stake_program_id,
                {
                    "encoding": "jsonParsed",
                    "limit": limit,  # Reduced from 100 to 50 to avoid RPC limits
                    # Add a filter to only get accounts with delegation
                    "filters": [
                        {
                            "memcmp": {
                                "offset": 4,  # Offset for StakeState enum
                                "bytes": "2"  # Only get accounts with delegation (delegated state)
                            }
                        }
                    ]
                }
            ]
            
            result = self._make_rpc_request("getProgramAccounts", params)
            
            # If we got some results, try to store them
            if result:
                try:
                    epoch_info = self.get_epoch_info()
                    current_epoch = epoch_info.get("epoch", 0)
                    
                    # Process the data to store in database
                    from utils.data_processor import DataProcessor
                    processor = DataProcessor(None, None, result)  
                    stake_data = processor.get_processed_stake_info()
                    
                    # Store in database
                    store_stake_accounts(stake_data, current_epoch)
                except Exception as e:
                    print(f"Warning: Failed to store stake account data: {str(e)}")
            
            return result
        except Exception as e:
            # Return an empty list instead of raising an exception
            # This allows the dashboard to partially work even if stake accounts can't be fetched
            print(f"Warning: Failed to get stake accounts: {str(e)}")
            return []
