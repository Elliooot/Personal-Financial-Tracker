"""
Currency utility functions for exchange rate calculations.
These functions are used by both views and signal handlers.
"""

import requests
from decimal import Decimal
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_exchange_rate_with_gbp_base(currency_code):
    """
    Calculate exchange rate with GBP as base currency using Open Exchange Rates API.
    
    This function works with the free tier of Open Exchange Rates by:
    1. Getting USD rates for both GBP and the target currency
    2. Calculating the cross rate between them
    
    Args:
        currency_code (str): Target currency code (e.g., 'EUR', 'JPY')
        
    Returns:
        Decimal: Exchange rate as GBP to target currency
    """
    API_KEY = settings.OPENEXCHANGERATES_API_KEY
    
    # If the target is GBP, return 1.0
    if currency_code == 'GBP':
        return Decimal('1.0')
    
    try:
        # We need both GBP and the target currency rates against USD
        url = "https://openexchangerates.org/api/latest.json"
        params = {
            'app_id': API_KEY,
            'base': 'USD',  # Free tier only supports USD as base
            'symbols': f"GBP,{currency_code}"  # Get both GBP and target rates
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' not in data:
            logger.error(f"Invalid API response: {data}")
            raise Exception("Invalid API response: 'rates' field missing")
        
        # Extract rates
        if 'GBP' not in data['rates'] or currency_code not in data['rates']:
            missing = []
            if 'GBP' not in data['rates']:
                missing.append('GBP')
            if currency_code not in data['rates']:
                missing.append(currency_code)
            raise Exception(f"Currency rates not found in response: {', '.join(missing)}")
        
        # Get USD to GBP and USD to target rates
        usd_to_gbp = Decimal(str(data['rates']['GBP']))
        usd_to_target = Decimal(str(data['rates'][currency_code]))
        
        # Calculate GBP to target rate:
        # GBP to target = (USD to target) / (USD to GBP)
        gbp_to_target = usd_to_target / usd_to_gbp
        
        logger.info(f"Calculated GBP to {currency_code} rate: {gbp_to_target}")
        return gbp_to_target
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise Exception(f"Failed to fetch exchange rate: {str(e)}")
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing API response: {str(e)}")
        raise Exception(f"Failed to parse exchange rate data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise Exception(f"Failed to get exchange rate: {str(e)}")


def get_multiple_rates_with_gbp_base(currency_codes):
    """
    Get multiple exchange rates with GBP as base currency in a single API call.
    
    Args:
        currency_codes (list): List of currency codes to get rates for
        
    Returns:
        dict: Dictionary of currency codes to exchange rates (GBP as base)
    """
    API_KEY = settings.OPENEXCHANGERATES_API_KEY
    
    # Filter out GBP if it's in the list (it would always be 1.0)
    codes_to_fetch = [code for code in currency_codes if code != 'GBP']
    
    # If only GBP was requested, return immediately
    if not codes_to_fetch:
        return {'GBP': Decimal('1.0')}
    
    # Add GBP to the list of currencies to fetch
    if 'GBP' not in codes_to_fetch:
        codes_to_fetch.append('GBP')
    
    try:
        # Prepare API call
        url = "https://openexchangerates.org/api/latest.json"
        params = {
            'app_id': API_KEY,
            'base': 'USD',
            'symbols': ','.join(codes_to_fetch)
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' not in data or 'GBP' not in data['rates']:
            logger.error(f"Invalid API response or GBP rate missing: {data}")
            raise Exception("Invalid API response: required rates missing")
        
        # Get the USD to GBP rate
        usd_to_gbp = Decimal(str(data['rates']['GBP']))
        
        # Calculate all rates with GBP as base
        result = {'GBP': Decimal('1.0')}  # GBP to GBP is always 1.0
        
        for code in currency_codes:
            if code == 'GBP':
                continue  # Already added
                
            if code in data['rates']:
                # Convert: GBP to target = (USD to target) / (USD to GBP)
                usd_to_target = Decimal(str(data['rates'][code]))
                gbp_to_target = usd_to_target / usd_to_gbp
                result[code] = gbp_to_target
            else:
                logger.warning(f"Currency {code} not found in API response")
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching multiple exchange rates: {str(e)}")
        raise Exception(f"Failed to fetch exchange rates: {str(e)}")