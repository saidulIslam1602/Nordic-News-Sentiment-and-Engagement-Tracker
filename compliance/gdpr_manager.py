"""
GDPR Compliance Manager

Handles GDPR compliance requirements including:
- User consent management
- Data anonymization and pseudonymization
- Right to be forgotten
- Data portability
- Data retention policies
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yaml
import os
from cryptography.fernet import Fernet
import uuid

logger = logging.getLogger(__name__)


class GDPRManager:
    """
    Manages GDPR compliance for the Nordic News Analytics platform.
    
    Features:
    - User consent tracking and management
    - Data anonymization and pseudonymization
    - Right to be forgotten implementation
    - Data portability and export
    - Data retention policy enforcement
    - Audit trail maintenance
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the GDPR manager."""
        self.config = self._load_config(config_path)
        self.consent_records = {}
        self.anonymization_key = self._generate_anonymization_key()
        self.audit_log = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return {}
    
    def _generate_anonymization_key(self) -> str:
        """Generate a key for data anonymization."""
        return Fernet.generate_key()
    
    def _log_audit_event(self, event_type: str, user_id: str, details: Dict):
        """Log an audit event for compliance tracking."""
        audit_event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details,
            'event_id': str(uuid.uuid4())
        }
        self.audit_log.append(audit_event)
        logger.info(f"Audit event: {event_type} for user {user_id}")
    
    def record_consent(self, user_id: str, consent_data: Dict) -> bool:
        """
        Record user consent for data processing.
        
        Args:
            user_id: User identifier
            consent_data: Consent information including purposes and timestamp
        
        Returns:
            True if consent was recorded successfully
        """
        try:
            consent_record = {
                'user_id': user_id,
                'consent_given': consent_data.get('consent_given', False),
                'purposes': consent_data.get('purposes', []),
                'timestamp': consent_data.get('timestamp', datetime.now().isoformat()),
                'ip_address': consent_data.get('ip_address'),
                'user_agent': consent_data.get('user_agent'),
                'consent_version': consent_data.get('consent_version', '1.0'),
                'withdrawal_timestamp': None
            }
            
            self.consent_records[user_id] = consent_record
            
            # Log audit event
            self._log_audit_event('consent_recorded', user_id, {
                'consent_given': consent_record['consent_given'],
                'purposes': consent_record['purposes']
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording consent: {e}")
            return False
    
    def withdraw_consent(self, user_id: str) -> bool:
        """
        Withdraw user consent for data processing.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if consent was withdrawn successfully
        """
        try:
            if user_id not in self.consent_records:
                logger.warning(f"No consent record found for user {user_id}")
                return False
            
            self.consent_records[user_id]['consent_given'] = False
            self.consent_records[user_id]['withdrawal_timestamp'] = datetime.now().isoformat()
            
            # Log audit event
            self._log_audit_event('consent_withdrawn', user_id, {
                'withdrawal_timestamp': self.consent_records[user_id]['withdrawal_timestamp']
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error withdrawing consent: {e}")
            return False
    
    def has_valid_consent(self, user_id: str, purpose: str) -> bool:
        """
        Check if user has valid consent for a specific purpose.
        
        Args:
            user_id: User identifier
            purpose: Data processing purpose
        
        Returns:
            True if user has valid consent
        """
        if user_id not in self.consent_records:
            return False
        
        consent_record = self.consent_records[user_id]
        
        # Check if consent is still valid
        if not consent_record['consent_given']:
            return False
        
        # Check if consent has been withdrawn
        if consent_record['withdrawal_timestamp']:
            return False
        
        # Check if purpose is covered by consent
        if purpose not in consent_record['purposes']:
            return False
        
        return True
    
    def anonymize_user_data(self, user_id: str, data: Dict) -> Dict:
        """
        Anonymize user data by removing or pseudonymizing personal information.
        
        Args:
            user_id: User identifier
            data: Data to anonymize
        
        Returns:
            Anonymized data dictionary
        """
        try:
            anonymized_data = data.copy()
            
            # Remove direct identifiers
            direct_identifiers = ['email', 'phone', 'address', 'name', 'ip_address']
            for identifier in direct_identifiers:
                if identifier in anonymized_data:
                    del anonymized_data[identifier]
            
            # Pseudonymize user ID
            if 'user_id' in anonymized_data:
                anonymized_data['user_id'] = self._pseudonymize_user_id(user_id)
            
            # Anonymize timestamps (keep relative timing but remove absolute dates)
            if 'timestamp' in anonymized_data:
                anonymized_data['timestamp'] = self._anonymize_timestamp(anonymized_data['timestamp'])
            
            # Log audit event
            self._log_audit_event('data_anonymized', user_id, {
                'original_fields': list(data.keys()),
                'anonymized_fields': list(anonymized_data.keys())
            })
            
            return anonymized_data
            
        except Exception as e:
            logger.error(f"Error anonymizing data: {e}")
            return data
    
    def _pseudonymize_user_id(self, user_id: str) -> str:
        """Create a pseudonymized version of user ID."""
        salt = self.anonymization_key.decode()
        return hashlib.sha256(f"{user_id}:{salt}".encode()).hexdigest()[:16]
    
    def _anonymize_timestamp(self, timestamp: str) -> str:
        """Anonymize timestamp by rounding to nearest hour."""
        try:
            dt = datetime.fromisoformat(timestamp)
            # Round to nearest hour
            rounded_dt = dt.replace(minute=0, second=0, microsecond=0)
            return rounded_dt.isoformat()
        except:
            return timestamp
    
    def delete_user_data(self, user_id: str) -> bool:
        """
        Delete all user data (Right to be Forgotten).
        
        Args:
            user_id: User identifier
        
        Returns:
            True if data was deleted successfully
        """
        try:
            # This would typically involve database operations
            # For now, we'll just log the request
            
            # Log audit event
            self._log_audit_event('data_deletion_requested', user_id, {
                'deletion_timestamp': datetime.now().isoformat()
            })
            
            # In a real implementation, this would:
            # 1. Delete user data from all tables
            # 2. Delete associated engagement events
            # 3. Delete sentiment analysis data
            # 4. Delete consent records
            # 5. Confirm deletion completion
            
            logger.info(f"Data deletion requested for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            return False
    
    def export_user_data(self, user_id: str) -> Dict:
        """
        Export user data in a portable format (Data Portability).
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary containing user's data
        """
        try:
            # This would typically involve database queries
            # For now, we'll return a sample structure
            
            user_data = {
                'user_id': user_id,
                'export_timestamp': datetime.now().isoformat(),
                'consent_records': self.consent_records.get(user_id, {}),
                'data_categories': [
                    'engagement_events',
                    'sentiment_preferences',
                    'content_interactions'
                ],
                'note': 'This is a sample export. In production, this would contain actual user data.'
            }
            
            # Log audit event
            self._log_audit_event('data_export_requested', user_id, {
                'export_timestamp': user_data['export_timestamp']
            })
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            return {}
    
    def get_data_retention_status(self, user_id: str) -> Dict:
        """
        Get data retention status for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with retention information
        """
        try:
            retention_days = self.config.get('gdpr', {}).get('data_retention_days', 365)
            
            # Calculate retention status
            if user_id in self.consent_records:
                consent_timestamp = datetime.fromisoformat(
                    self.consent_records[user_id]['timestamp']
                )
                days_since_consent = (datetime.now() - consent_timestamp).days
                
                retention_status = {
                    'user_id': user_id,
                    'consent_given': self.consent_records[user_id]['consent_given'],
                    'consent_timestamp': self.consent_records[user_id]['timestamp'],
                    'days_since_consent': days_since_consent,
                    'retention_limit_days': retention_days,
                    'days_until_expiry': max(0, retention_days - days_since_consent),
                    'should_be_deleted': days_since_consent > retention_days
                }
            else:
                retention_status = {
                    'user_id': user_id,
                    'consent_given': False,
                    'consent_timestamp': None,
                    'days_since_consent': None,
                    'retention_limit_days': retention_days,
                    'days_until_expiry': 0,
                    'should_be_deleted': True
                }
            
            return retention_status
            
        except Exception as e:
            logger.error(f"Error getting retention status: {e}")
            return {}
    
    def cleanup_expired_data(self) -> int:
        """
        Clean up data that has exceeded retention period.
        
        Returns:
            Number of records cleaned up
        """
        try:
            cleanup_count = 0
            retention_days = self.config.get('gdpr', {}).get('data_retention_days', 365)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Find users with expired data
            expired_users = []
            for user_id, consent_record in self.consent_records.items():
                consent_timestamp = datetime.fromisoformat(consent_record['timestamp'])
                if consent_timestamp < cutoff_date:
                    expired_users.append(user_id)
            
            # Clean up expired data
            for user_id in expired_users:
                if self.delete_user_data(user_id):
                    cleanup_count += 1
                    # Remove from consent records
                    del self.consent_records[user_id]
            
            # Log audit event
            self._log_audit_event('data_cleanup', 'system', {
                'cleanup_timestamp': datetime.now().isoformat(),
                'records_cleaned': cleanup_count,
                'retention_days': retention_days
            })
            
            logger.info(f"Cleaned up {cleanup_count} expired records")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {e}")
            return 0
    
    def get_audit_log(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        Get audit log for compliance reporting.
        
        Args:
            user_id: Optional user ID to filter by
        
        Returns:
            List of audit events
        """
        if user_id:
            return [event for event in self.audit_log if event['user_id'] == user_id]
        else:
            return self.audit_log
    
    def generate_compliance_report(self) -> Dict:
        """Generate a GDPR compliance report."""
        try:
            total_users = len(self.consent_records)
            users_with_consent = sum(1 for record in self.consent_records.values() 
                                   if record['consent_given'])
            users_withdrawn = sum(1 for record in self.consent_records.values() 
                                if record['withdrawal_timestamp'])
            
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'total_users': total_users,
                'users_with_consent': users_with_consent,
                'users_withdrawn_consent': users_withdrawn,
                'consent_rate': (users_with_consent / total_users * 100) if total_users > 0 else 0,
                'data_retention_days': self.config.get('gdpr', {}).get('data_retention_days', 365),
                'audit_events_count': len(self.audit_log),
                'compliance_status': 'COMPLIANT' if users_with_consent > 0 else 'NON_COMPLIANT'
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {}


def main():
    """Main function for testing the GDPR manager."""
    gdpr = GDPRManager()
    
    # Test consent recording
    test_consent = {
        'consent_given': True,
        'purposes': ['analytics', 'personalization', 'marketing'],
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0...',
        'consent_version': '1.0'
    }
    
    success = gdpr.record_consent('user_001', test_consent)
    print(f"Consent recorded: {success}")
    
    # Test consent validation
    has_consent = gdpr.has_valid_consent('user_001', 'analytics')
    print(f"Has consent for analytics: {has_consent}")
    
    # Test data anonymization
    test_data = {
        'user_id': 'user_001',
        'email': 'user@example.com',
        'timestamp': '2024-01-15T10:30:00',
        'engagement_score': 0.85
    }
    
    anonymized = gdpr.anonymize_user_data('user_001', test_data)
    print(f"Anonymized data: {anonymized}")
    
    # Test data export
    export_data = gdpr.export_user_data('user_001')
    print(f"Export data: {export_data}")
    
    # Generate compliance report
    report = gdpr.generate_compliance_report()
    print(f"Compliance report: {report}")


if __name__ == "__main__":
    main()