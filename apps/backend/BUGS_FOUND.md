# Bugs Found During Browser Testing

## Bug #1: Supabase Email Validation Issue
**Severity:** Medium  
**Location:** Frontend - Signup page (`/app/signup`)  
**Description:** Supabase rejects valid email address `test@example.com` with error "Email address is invalid"  
**Error:** 400 response from Supabase auth endpoint  
**Console Error:** `Signup error: Email address "test@example.com" is invalid`  
**Note:** `testuser2025@gmail.com` format works successfully  
**Impact:** Some valid email formats may be rejected (possibly Supabase configuration issue)

## Bug #2: Signup Success Treated as Error
**Severity:** Low (UI/UX)  
**Location:** Frontend - Signup page (`/app/signup`)  
**Description:** Successful signup with email verification requirement is logged as an error in console  
**Console Error:** `Signup error: Error: Please check your email to verify your account`  
**Expected Behavior:** Email verification message should be handled as success, not error  
**Impact:** Misleading console errors, potentially confusing developers  
**Note:** Signup actually succeeds, user sees correct message "Please check your email to verify your account"

## Bug #3: Chat Responses Have Significant Delay
**Severity:** High  
**Location:** Backend/Frontend - Chat interface (`/app/quote`)  
**Description:** Chat messages eventually receive responses, but with extremely long delays (20+ seconds). This makes the chat interface feel unresponsive.  
**Steps to Reproduce:** 
1. Navigate to `/app/quote` (authenticated)
2. Type a message: "I need a quote for a trip to Japan"
3. Press Enter or click send
4. Wait 20+ seconds for response to appear
**Network Requests:** 
- `POST /api/v1/chat/session` - Called successfully
- `POST /api/v1/chat/message` - Called successfully, but slow response
**Expected Behavior:** Assistant should respond within 2-5 seconds  
**Actual Behavior:** Response takes 20+ seconds to appear  
**Impact:** Poor user experience - chat feels broken/unresponsive  
**Note:** Likely backend processing issue (LLM calls, LangGraph execution taking too long). Response eventually appears, confirming functionality works but performance is poor.

## Bug #4: Enter Key Not Sending Messages
**Severity:** Medium  
**Location:** Frontend - Chat interface (`/app/quote`)  
**Description:** Pressing Enter in the message textbox does not send the message. Only clicking the send button works.  
**Steps to Reproduce:** 
1. Navigate to `/app/quote` (authenticated)
2. Type a message in the textbox
3. Press Enter
4. Message does not send (remains in textbox)
5. Click send button - message sends successfully
**Expected Behavior:** Pressing Enter should send the message, same as clicking send button  
**Actual Behavior:** Enter key does not trigger send, only button click works  
**Impact:** Poor UX - users expect Enter to work for sending messages

## Status
- **Total Bugs Found:** 4
- **Critical:** 0
- **High:** 1
- **Medium:** 2
- **Low:** 1

