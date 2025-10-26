"""
Upload Agent for DeFi Payroll Manager
Handles CSV file processing and validation for employee payroll data
"""

import pandas as pd
import io
import json
from typing import List, Dict, Any, Optional, Tuple
import re
from decimal import Decimal, InvalidOperation

class UploadAgent:
    """
    Specialized agent for processing payroll CSV uploads and data validation
    """
    
    def __init__(self):
        self.supported_tokens = {
            'ETH', 'USDC', 'USDT', 'DAI', 'WETH', 'MATIC', 'WBTC', 'UNI', 'LINK', 'AAVE'
        }
        self.required_columns = ['employee_address', 'from_token', 'to_token', 'amount']
        
    def validate_ethereum_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        if not address or not isinstance(address, str):
            return False
        
        # Remove whitespace
        address = address.strip()
        
        # Check if it starts with 0x and has correct length
        if not address.startswith('0x') or len(address) != 42:
            return False
            
        # Check if it contains only valid hex characters
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False
    
    def validate_token_symbol(self, token: str) -> bool:
        """Validate token symbol"""
        if not token or not isinstance(token, str):
            return False
        return token.upper().strip() in self.supported_tokens
    
    def validate_amount(self, amount: Any) -> Tuple[bool, Optional[float]]:
        """Validate and convert amount to float"""
        try:
            if isinstance(amount, str):
                # Remove any currency symbols or whitespace
                amount = re.sub(r'[^\d.-]', '', amount.strip())
            
            decimal_amount = Decimal(str(amount))
            float_amount = float(decimal_amount)
            
            # Check if amount is positive and reasonable
            if float_amount <= 0 or float_amount > 1000000:  # Max $1M per employee
                return False, None
                
            return True, float_amount
        except (InvalidOperation, ValueError, TypeError):
            return False, None
    
    def process_csv_content(self, csv_content: str) -> Dict[str, Any]:
        """
        Process CSV content and return structured payroll data
        """
        try:
            # Read CSV content
            df = pd.read_csv(io.StringIO(csv_content))
            
            # Normalize column names (remove spaces, convert to lowercase)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Check required columns
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                return {
                    'success': False,
                    'error': f'Missing required columns: {", ".join(missing_columns)}',
                    'required_columns': self.required_columns,
                    'found_columns': list(df.columns)
                }
            
            # Process each row
            processed_data = []
            validation_errors = []
            
            for index, row in df.iterrows():
                row_errors = []
                
                # Validate employee address
                employee_address = str(row['employee_address']).strip()
                if not self.validate_ethereum_address(employee_address):
                    row_errors.append(f"Invalid Ethereum address: {employee_address}")
                
                # Validate from_token
                from_token = str(row['from_token']).strip().upper()
                if not self.validate_token_symbol(from_token):
                    row_errors.append(f"Unsupported from_token: {from_token}")
                
                # Validate to_token
                to_token = str(row['to_token']).strip().upper()
                if not self.validate_token_symbol(to_token):
                    row_errors.append(f"Unsupported to_token: {to_token}")
                
                # Validate amount
                amount_valid, amount_value = self.validate_amount(row['amount'])
                if not amount_valid:
                    row_errors.append(f"Invalid amount: {row['amount']}")
                
                if row_errors:
                    validation_errors.append({
                        'row': index + 2,  # +2 because pandas is 0-indexed and CSV has header
                        'errors': row_errors
                    })
                else:
                    processed_data.append({
                        'employee_address': employee_address,
                        'from_token': from_token,
                        'to_token': to_token,
                        'amount': amount_value,
                        'row_number': index + 2
                    })
            
            # Generate summary statistics
            if processed_data:
                total_amount = sum(emp['amount'] for emp in processed_data)
                token_breakdown = {}
                
                for emp in processed_data:
                    from_token = emp['from_token']
                    to_token = emp['to_token']
                    
                    if from_token not in token_breakdown:
                        token_breakdown[from_token] = {'outgoing': 0, 'incoming': 0}
                    if to_token not in token_breakdown:
                        token_breakdown[to_token] = {'outgoing': 0, 'incoming': 0}
                    
                    token_breakdown[from_token]['outgoing'] += emp['amount']
                    token_breakdown[to_token]['incoming'] += emp['amount']
                
                summary = {
                    'total_employees': len(processed_data),
                    'total_amount_usd': total_amount,
                    'unique_tokens': len(set([emp['from_token'] for emp in processed_data] + 
                                           [emp['to_token'] for emp in processed_data])),
                    'token_breakdown': token_breakdown,
                    'average_payment': total_amount / len(processed_data),
                    'payment_range': {
                        'min': min(emp['amount'] for emp in processed_data),
                        'max': max(emp['amount'] for emp in processed_data)
                    }
                }
            else:
                summary = None
            
            return {
                'success': True,
                'data': processed_data,
                'summary': summary,
                'validation_errors': validation_errors,
                'total_rows_processed': len(df),
                'valid_rows': len(processed_data),
                'error_rows': len(validation_errors)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to process CSV: {str(e)}',
                'details': 'Please ensure your CSV file is properly formatted with the required columns.'
            }
    
    def generate_netting_analysis(self, payroll_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze netting opportunities for the payroll batch
        """
        if not payroll_data:
            return {'error': 'No payroll data provided'}
        
        # Calculate token flows
        token_flows = {}
        for payment in payroll_data:
            from_token = payment['from_token']
            to_token = payment['to_token']
            amount = payment['amount']
            
            # Track outflows
            if from_token not in token_flows:
                token_flows[from_token] = {'out': 0, 'in': 0}
            token_flows[from_token]['out'] += amount
            
            # Track inflows
            if to_token not in token_flows:
                token_flows[to_token] = {'out': 0, 'in': 0}
            token_flows[to_token]['in'] += amount
        
        # Calculate net positions
        net_positions = {}
        for token, flows in token_flows.items():
            net_positions[token] = flows['in'] - flows['out']
        
        # Calculate netting savings
        original_transactions = len(payroll_data)
        
        # Estimate netted transactions (simplified logic)
        tokens_with_net_outflow = sum(1 for net in net_positions.values() if net < 0)
        tokens_with_net_inflow = sum(1 for net in net_positions.values() if net > 0)
        estimated_netted_transactions = max(tokens_with_net_outflow, tokens_with_net_inflow, 1)
        
        # Calculate savings
        gas_per_transaction = 12.50  # USD
        original_gas_cost = original_transactions * gas_per_transaction
        netted_gas_cost = estimated_netted_transactions * gas_per_transaction
        gas_savings = original_gas_cost - netted_gas_cost
        savings_percentage = (gas_savings / original_gas_cost) * 100 if original_gas_cost > 0 else 0
        
        return {
            'original_transactions': original_transactions,
            'netted_transactions': estimated_netted_transactions,
            'gas_savings_usd': round(gas_savings, 2),
            'savings_percentage': round(savings_percentage, 1),
            'original_gas_cost': round(original_gas_cost, 2),
            'netted_gas_cost': round(netted_gas_cost, 2),
            'token_flows': token_flows,
            'net_positions': net_positions,
            'execution_time_estimate': f"{estimated_netted_transactions * 15} seconds",
            'mev_protection': 'Full protection through internal netting'
        }
    
    def validate_csv_format(self, csv_content: str) -> Dict[str, Any]:
        """
        Quick validation of CSV format without full processing
        """
        try:
            # Try to read just the header
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return {
                    'valid': False,
                    'error': 'CSV file must contain at least a header and one data row'
                }
            
            # Check header
            header = lines[0].lower().strip()
            required_cols = ['employee_address', 'from_token', 'to_token', 'amount']
            
            missing_cols = []
            for col in required_cols:
                if col not in header:
                    missing_cols.append(col)
            
            if missing_cols:
                return {
                    'valid': False,
                    'error': f'Missing required columns: {", ".join(missing_cols)}',
                    'required_columns': required_cols
                }
            
            return {
                'valid': True,
                'rows_detected': len(lines) - 1,
                'columns_detected': len(lines[0].split(','))
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Invalid CSV format: {str(e)}'
            }
    
    def generate_sample_csv(self) -> str:
        """
        Generate a sample CSV template for users
        """
        sample_data = [
            ['employee_address', 'from_token', 'to_token', 'amount'],
            ['0x1234567890123456789012345678901234567890', 'USDC', 'ETH', '2500'],
            ['0x2345678901234567890123456789012345678901', 'USDC', 'USDC', '3000'],
            ['0x3456789012345678901234567890123456789012', 'USDC', 'MATIC', '2800'],
            ['0x4567890123456789012345678901234567890123', 'USDC', 'ETH', '3200'],
            ['0x5678901234567890123456789012345678901234', 'USDC', 'DAI', '2700']
        ]
        
        return '\n'.join([','.join(row) for row in sample_data])

# Example usage and testing
if __name__ == "__main__":
    agent = UploadAgent()
    
    # Test with sample CSV
    sample_csv = agent.generate_sample_csv()
    result = agent.process_csv_content(sample_csv)
    
    print("Sample CSV Processing Result:")
    print(json.dumps(result, indent=2))
    
    if result['success'] and result['data']:
        netting_analysis = agent.generate_netting_analysis(result['data'])
        print("\nNetting Analysis:")
        print(json.dumps(netting_analysis, indent=2))