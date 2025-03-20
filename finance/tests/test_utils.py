from django.test import TestCase
from unittest import mock
from decimal import Decimal
import json
from contextlib import contextmanager
import requests

from django.conf import settings

from finance.currency_utils import (
    get_exchange_rate_with_gbp_base,
    get_multiple_rates_with_gbp_base
)
from finance.models import Currency

class MockResponse:
    def __init__(self, json_data, status_code=200, headers=None, reason=None):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = headers or {}
        self.reason = reason or ""
        self.content = json.dumps(json_data).encode('utf-8')
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"HTTP Error: {self.status_code} {self.reason}", response=self)


class CurrencyUtilsEnhancedTest(TestCase):
    def setUp(self):
        # Create some test Currency records
        Currency.objects.create(
            user=None,
            currency_code='GBP',
            exchange_rate=Decimal('1.0')
        )
        Currency.objects.create(
            user=None,
            currency_code='EUR',
            exchange_rate=Decimal('1.15')
        )
        Currency.objects.create(
            user=None,
            currency_code='USD',
            exchange_rate=Decimal('1.25')
        )
        
    @contextmanager
    def settings_api_key(self, key='test_key'):
        """Context manager to temporarily set the API key in settings"""
        with self.settings(OPENEXCHANGERATES_API_KEY=key):
            yield
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_exchange_rate_gbp_base(self, mock_get):
        """Test calculating exchange rate with GBP as base currency"""
        # Mock successful API response
        mock_response = MockResponse({
            "disclaimer": "Usage subject to terms: https://openexchangerates.org/terms",
            "license": "https://openexchangerates.org/license",
            "timestamp": 1647270000,
            "base": "USD",
            "rates": {
                "GBP": 0.75,
                "EUR": 0.90,
                "JPY": 115.0
            }
        })
        mock_get.return_value = mock_response
        
        with self.settings_api_key():
            # Test EUR rate: (USD to EUR) / (USD to GBP) = 0.90 / 0.75 = 1.2
            eur_rate = get_exchange_rate_with_gbp_base('EUR')
            self.assertEqual(eur_rate, Decimal('1.2'))
            
            # Verify API call parameters
            mock_get.assert_called_with(
                "https://openexchangerates.org/api/latest.json",
                params={
                    'app_id': 'test_key',
                    'base': 'USD',
                    'symbols': 'GBP,EUR'
                },
                timeout=10
            )
            
            # Reset mock for next call
            mock_get.reset_mock()
            
            # Test JPY rate
            jpy_rate = get_exchange_rate_with_gbp_base('JPY')
            self.assertEqual(jpy_rate, Decimal('153.3333333333333333333333333'))
            
            # Verify new API call parameters (different currency)
            mock_get.assert_called_with(
                "https://openexchangerates.org/api/latest.json",
                params={
                    'app_id': 'test_key',
                    'base': 'USD',
                    'symbols': 'GBP,JPY'
                },
                timeout=10
            )
    
    def test_get_exchange_rate_gbp_to_gbp(self):
        """Test getting GBP to GBP exchange rate (should always be 1.0)"""
        # This should return 1.0 without making any API call
        with self.settings_api_key():
            rate = get_exchange_rate_with_gbp_base('GBP')
            self.assertEqual(rate, Decimal('1.0'))
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_exchange_rate_api_error(self, mock_get):
        """Test handling of API errors"""
        # Mock HTTP error
        mock_get.return_value = MockResponse(
            {"error": "Invalid app_id parameter"}, 
            status_code=401,
            reason="Unauthorized"
        )
        
        with self.settings_api_key('invalid_key'):
            with self.assertRaises(Exception) as context:
                get_exchange_rate_with_gbp_base('EUR')
                
            self.assertIn('Failed to fetch exchange rate', str(context.exception))
            self.assertIn('HTTP Error: 401', str(context.exception))
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_exchange_rate_network_error(self, mock_get):
        """Test handling of network errors"""
        # Simulate network error
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        with self.settings_api_key():
            with self.assertRaises(Exception) as context:
                get_exchange_rate_with_gbp_base('EUR')
                
            self.assertIn('Failed to fetch exchange rate', str(context.exception))
            self.assertIn('Connection refused', str(context.exception))
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_exchange_rate_missing_rates(self, mock_get):
        """Test handling of missing rates in API response"""
        # Mock response with missing rates
        mock_response = MockResponse({
            "disclaimer": "Usage subject to terms",
            "license": "https://openexchangerates.org/license",
            "timestamp": 1647270000,
            "base": "USD",
            "rates": {
                "GBP": 0.75
                # EUR is missing
            }
        })
        mock_get.return_value = mock_response
        
        with self.settings_api_key():
            with self.assertRaises(Exception) as context:
                get_exchange_rate_with_gbp_base('EUR')
                
            self.assertIn('Currency rates not found', str(context.exception))
            self.assertIn('EUR', str(context.exception))
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_exchange_rate_invalid_response(self, mock_get):
        """Test handling of invalid API response format"""
        # Mock invalid response (missing rates key)
        mock_response = MockResponse({
            "disclaimer": "Usage subject to terms",
            "error": "Some error occurred"
            # Missing 'rates' key
        })
        mock_get.return_value = mock_response
        
        with self.settings_api_key():
            with self.assertRaises(Exception) as context:
                get_exchange_rate_with_gbp_base('EUR')
                
            self.assertIn("Invalid API response: 'rates' field missing", str(context.exception))
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_exchange_rate_timeout(self, mock_get):
        """Test handling of API timeout"""
        # Simulate timeout
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        with self.settings_api_key():
            with self.assertRaises(Exception) as context:
                get_exchange_rate_with_gbp_base('EUR')
                
            self.assertIn('Failed to fetch exchange rate', str(context.exception))
            self.assertIn('Request timed out', str(context.exception))
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_multiple_rates_success(self, mock_get):
        """Test getting multiple exchange rates in one API call"""
        # Mock API response
        mock_response = MockResponse({
            "disclaimer": "Usage subject to terms",
            "timestamp": 1647270000,
            "base": "USD",
            "rates": {
                "GBP": 0.75,
                "EUR": 0.90,
                "JPY": 115.0,
                "AUD": 1.35
            }
        })
        mock_get.return_value = mock_response
        
        with self.settings_api_key():
            # Request multiple rates
            rates = get_multiple_rates_with_gbp_base(['EUR', 'JPY', 'AUD', 'GBP'])
            
            # Verify results
            self.assertEqual(len(rates), 4)
            self.assertEqual(rates['GBP'], Decimal('1.0'))
            self.assertEqual(rates['EUR'], Decimal('1.2'))  # 0.90 / 0.75
            self.assertEqual(rates['JPY'], Decimal('153.3333333333333333333333333'))  # 115.0 / 0.75
            self.assertEqual(rates['AUD'], Decimal('1.8'))  # 1.35 / 0.75
            
            # Verify API was called correctly
            mock_get.assert_called_once()
            call_args = mock_get.call_args[1]
            self.assertEqual(call_args['params']['app_id'], 'test_key')
            self.assertEqual(call_args['params']['base'], 'USD')
            
            # The order of currencies in the API call may vary, so check they're all included
            symbols = call_args['params']['symbols'].split(',')
            self.assertIn('GBP', symbols)
            self.assertIn('EUR', symbols)
            self.assertIn('JPY', symbols)
            self.assertIn('AUD', symbols)
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_multiple_rates_some_missing(self, mock_get):
        """Test getting multiple rates when some currencies are missing from API response"""
        # Mock API response with some currencies missing
        mock_response = MockResponse({
            "disclaimer": "Usage subject to terms",
            "timestamp": 1647270000,
            "base": "USD",
            "rates": {
                "GBP": 0.75,
                "EUR": 0.90,
                # JPY is missing
                "AUD": 1.35
            }
        })
        mock_get.return_value = mock_response
        
        with self.settings_api_key():
            # Request multiple rates including one that's missing
            rates = get_multiple_rates_with_gbp_base(['EUR', 'JPY', 'AUD', 'GBP'])
            
            # Verify results (JPY should be missing)
            self.assertEqual(len(rates), 3)
            self.assertEqual(rates['GBP'], Decimal('1.0'))
            self.assertEqual(rates['EUR'], Decimal('1.2'))
            self.assertEqual(rates['AUD'], Decimal('1.8'))
            self.assertNotIn('JPY', rates)
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_multiple_rates_gbp_only(self, mock_get):
        """Test getting multiple rates when only GBP is requested"""
        with self.settings_api_key():
            # Request only GBP
            rates = get_multiple_rates_with_gbp_base(['GBP'])
            
            # Verify result and that no API call was made
            self.assertEqual(len(rates), 1)
            self.assertEqual(rates['GBP'], Decimal('1.0'))
            mock_get.assert_not_called()
    
    @mock.patch('finance.currency_utils.requests.get')
    def test_get_multiple_rates_api_error(self, mock_get):
        """Test handling API errors when getting multiple rates"""
        # Mock HTTP error
        mock_get.return_value = MockResponse(
            {"error": "Invalid app_id parameter"}, 
            status_code=401,
            reason="Unauthorized"
        )
        
        with self.settings_api_key('invalid_key'):
            with self.assertRaises(Exception) as context:
                get_multiple_rates_with_gbp_base(['EUR', 'JPY'])
                
            self.assertIn('Failed to fetch exchange rates', str(context.exception))