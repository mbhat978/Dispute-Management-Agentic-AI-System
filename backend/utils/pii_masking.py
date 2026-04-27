"""
PII Masking Utility for Banking Dispute Management System

This module provides utilities to mask personally identifiable information (PII)
in logs, audit trails, and API responses to ensure compliance with data
protection regulations (GDPR, PCI DSS, etc.).
"""

import re
from typing import Any, Dict, List, Union


def mask_card_number(card_number: str) -> str:
    """
    Mask card number, showing only last 4 digits
    
    Args:
        card_number: Full card number (e.g., "4532123456789012")
        
    Returns:
        Masked card number (e.g., "****-****-****-9012")
    """
    if not card_number or not isinstance(card_number, str):
        return "****-****-****-****"
    
    # Remove any spaces or dashes
    clean_number = re.sub(r'[\s\-]', '', card_number)
    
    if len(clean_number) < 4:
        return "****-****-****-****"
    
    # Show only last 4 digits
    return f"****-****-****-{clean_number[-4:]}"


def mask_email(email: str) -> str:
    """
    Mask email address
    
    Args:
        email: Full email address (e.g., "john.doe@example.com")
        
    Returns:
        Masked email (e.g., "j***@example.com")
    """
    if not email or not isinstance(email, str) or "@" not in email:
        return "***@***.com"
    
    try:
        local, domain = email.split("@", 1)
        if len(local) <= 1:
            return f"*@{domain}"
        return f"{local[0]}***@{domain}"
    except:
        return "***@***.com"


def mask_phone(phone: str) -> str:
    """
    Mask phone number
    
    Args:
        phone: Full phone number (e.g., "555-123-4567")
        
    Returns:
        Masked phone (e.g., "***-***-4567")
    """
    if not phone or not isinstance(phone, str):
        return "***-***-****"
    
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) < 4:
        return "***-***-****"
    
    # Show only last 4 digits
    return f"***-***-{digits[-4:]}"


def mask_account_number(account_number: str) -> str:
    """
    Mask account number
    
    Args:
        account_number: Full account number
        
    Returns:
        Masked account number showing only last 4 digits
    """
    if not account_number or not isinstance(account_number, str):
        return "****"
    
    if len(account_number) < 4:
        return "****"
    
    return f"****{account_number[-4:]}"


def mask_ssn(ssn: str) -> str:
    """
    Mask Social Security Number
    
    Args:
        ssn: Full SSN (e.g., "123-45-6789")
        
    Returns:
        Masked SSN (e.g., "***-**-6789")
    """
    if not ssn or not isinstance(ssn, str):
        return "***-**-****"
    
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', ssn)
    
    if len(digits) < 4:
        return "***-**-****"
    
    # Show only last 4 digits
    return f"***-**-{digits[-4:]}"


def mask_sensitive_data(data: Union[Dict[str, Any], List, str, Any]) -> Union[Dict[str, Any], List, str, Any]:
    """
    Recursively mask all PII in a data structure
    
    This function handles nested dictionaries, lists, and various data types,
    automatically detecting and masking common PII fields.
    
    Args:
        data: Data structure to mask (dict, list, or primitive)
        
    Returns:
        Masked data structure with same type as input
        
    Example:
        >>> data = {
        ...     "customer": {
        ...         "name": "John Doe",
        ...         "email": "john@example.com",
        ...         "card_number": "4532123456789012"
        ...     }
        ... }
        >>> masked = mask_sensitive_data(data)
        >>> print(masked["customer"]["card_number"])
        "****-****-****-9012"
    """
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key indicates PII field
            if key_lower in ["card_number", "cardnumber", "card", "pan"]:
                masked[key] = mask_card_number(str(value)) if value else "****-****-****-****"
            elif key_lower in ["email", "email_address", "emailaddress"]:
                masked[key] = mask_email(str(value)) if value else "***@***.com"
            elif key_lower in ["phone", "phone_number", "phonenumber", "mobile", "mobile_number"]:
                masked[key] = mask_phone(str(value)) if value else "***-***-****"
            elif key_lower in ["ssn", "social_security_number", "socialsecuritynumber"]:
                masked[key] = mask_ssn(str(value)) if value else "***-**-****"
            elif key_lower in ["account_number", "accountnumber", "account", "bank_account"]:
                masked[key] = mask_account_number(str(value)) if value else "****"
            elif key_lower in ["password", "pwd", "secret", "token", "api_key", "apikey"]:
                masked[key] = "***REDACTED***"
            elif key_lower in ["cvv", "cvc", "security_code"]:
                masked[key] = "***"
            else:
                # Recursively mask nested structures
                masked[key] = mask_sensitive_data(value)
        
        return masked
    
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    
    elif isinstance(data, tuple):
        return tuple(mask_sensitive_data(item) for item in data)
    
    else:
        # Return primitive types as-is
        return data


def mask_audit_trail(audit_trail: List[str]) -> List[str]:
    """
    Mask PII in audit trail entries
    
    Args:
        audit_trail: List of audit trail strings
        
    Returns:
        List of masked audit trail strings
    """
    masked_trail = []
    
    # Patterns to mask in text
    patterns = [
        (r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', lambda m: mask_card_number(m.group())),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', lambda m: mask_email(m.group())),
        (r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{4}\b', lambda m: mask_phone(m.group())),
        (r'\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b', lambda m: mask_ssn(m.group())),
    ]
    
    for entry in audit_trail:
        masked_entry = entry
        for pattern, mask_func in patterns:
            masked_entry = re.sub(pattern, mask_func, masked_entry)
        masked_trail.append(masked_entry)
    
    return masked_trail


def is_pii_field(field_name: str) -> bool:
    """
    Check if a field name indicates it contains PII
    
    Args:
        field_name: Name of the field to check
        
    Returns:
        True if field likely contains PII
    """
    pii_keywords = [
        "card", "email", "phone", "mobile", "ssn", "social",
        "account", "password", "pwd", "secret", "token",
        "cvv", "cvc", "security_code", "pan", "name",
        "address", "dob", "birth", "passport", "license"
    ]
    
    field_lower = field_name.lower()
    return any(keyword in field_lower for keyword in pii_keywords)


def create_masked_copy(data: Dict[str, Any], fields_to_mask: List[str] | None = None) -> Dict[str, Any]:
    """
    Create a masked copy of data with specific fields masked
    
    Args:
        data: Original data dictionary
        fields_to_mask: List of field names to mask (if None, auto-detect PII)
        
    Returns:
        Masked copy of the data
    """
    if fields_to_mask is None:
        # Auto-detect PII fields
        fields_to_mask = [key for key in data.keys() if is_pii_field(key)]
    
    masked = data.copy()
    for field in fields_to_mask:
        if field in masked:
            masked[field] = "***MASKED***"
    
    return masked


def sanitize_for_logging(data: Any) -> Any:
    """
    Sanitize data for safe logging (removes all PII)
    
    This is a convenience function that applies comprehensive PII masking
    suitable for logging purposes.
    
    Args:
        data: Data to sanitize
        
    Returns:
        Sanitized data safe for logging
    """
    return mask_sensitive_data(data)


# Made with Bob - PII Masking Utility