# Refund Evidence Upload Feature

## Overview
Added support for uploading evidence documents when filing a "Refund Not Received" dispute. This feature allows customers to provide proof of their refund request, such as email confirmations, return receipts, or support chat screenshots.

## Changes Made

### 1. Mock Evidence Images Created
Generated three realistic mock evidence images for testing Test Case 8.1 (Merchant Refund Delayed):

**Location:** `sample_receipts/`

**Files:**
- `refund_evidence_email_screenshot.png` - Email from Fashion Store confirming refund approval
- `refund_evidence_return_receipt.png` - Return shipping receipt with tracking
- `refund_evidence_support_chat.png` - Support chat conversation about the return

**Test Case Details:**
- Customer: Meera Reddy (customer_id: 5)
- Merchant: Fashion Store
- Amount: $35.00
- Order: FS-2024-1357
- Scenario: Refund promised on January 10, 2024, but not received after 10+ days

### 2. Frontend UI Updates

**File:** `frontend/app/customer/page.tsx`

#### Added State Variable:
```typescript
const [refundEvidence, setRefundEvidence] = useState<File | null>(null);
```

#### Added Upload Section:
When customer selects "Refund Not Received" dispute type, a new section appears with:
- Clear instructions on what evidence to upload
- File upload button (accepts images and PDFs)
- List of acceptable evidence types:
  - Email confirmation from merchant
  - Return receipt or tracking information
  - Support chat/ticket screenshot
  - Any communication showing refund was promised
- Required field validation with warning message

#### Updated Form Logic:
1. **Reset on dispute type change:** Clears refund evidence when switching dispute types
2. **Validation:** Ensures evidence is uploaded before submission for refund disputes
3. **File handling:** Uses existing `convertFileToBase64` function to encode the file
4. **Query building:** Includes evidence filename in the comprehensive query sent to backend
5. **Form reset:** Clears refund evidence after successful submission

#### Visual Design:
- Orange-themed section (border-orange-200, bg-orange-50) to distinguish from other dispute types
- Warning icon and message if evidence not uploaded
- File name display with remove button after upload
- Consistent with existing UI patterns (matches merchant receipt upload)

## Usage

### For Testing:
1. Start the application
2. Login as Meera Reddy (customer_id: 5)
3. Select a transaction from Fashion Store
4. Choose "↩️ Refund Not Received" as dispute type
5. Upload one of the generated evidence images from `sample_receipts/`
6. Fill in the description
7. Submit the dispute

### Evidence Requirements:
- **Required:** For "Refund Not Received" disputes
- **Optional:** For other dispute types (merchant receipt field)
- **Accepted formats:** Images (PNG, JPG, etc.) and PDF files
- **Purpose:** Helps AI agents investigate and make informed decisions

## Backend Integration

The uploaded evidence is:
1. Converted to Base64 format
2. Sent to backend as `receipt_image_base64` parameter
3. Can be processed by vision-enabled AI agents for analysis
4. Stored with the dispute for audit trail

## Benefits

1. **Better Evidence:** Customers provide concrete proof of refund requests
2. **Faster Resolution:** AI agents can analyze evidence to make decisions
3. **Audit Trail:** Evidence is preserved for compliance and review
4. **User Experience:** Clear guidance on what to upload
5. **Validation:** Prevents submission without required evidence

## Future Enhancements

Potential improvements:
- Multiple file upload support
- Image preview before submission
- OCR to extract key information (dates, amounts, order numbers)
- Evidence quality validation
- Automatic evidence type detection