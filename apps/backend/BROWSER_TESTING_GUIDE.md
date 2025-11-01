# Browser Testing Guide

## Direct Browser Access Available ✅

I have **direct browser automation** capabilities through MCP browser tools. This means I can:

- ✅ Navigate to URLs directly
- ✅ Take screenshots/snapshots of pages
- ✅ Click buttons and interact with elements
- ✅ Type text into input fields
- ✅ Wait for elements to appear/disappear
- ✅ Read page content and verify UI state
- ✅ Test full user flows through the browser

## Available Browser Tools

The following browser automation tools are available:

### Navigation
- `browser_navigate(url)` - Navigate to a URL
- `browser_navigate_back()` - Go back in history
- `browser_resize(width, height)` - Resize browser window

### Interaction
- `browser_click(element_ref)` - Click an element
- `browser_type(element_ref, text)` - Type text into input
- `browser_hover(element_ref)` - Hover over element
- `browser_select_option(element_ref, values)` - Select dropdown option
- `browser_drag(start_ref, end_ref)` - Drag and drop

### Reading
- `browser_snapshot()` - Get accessibility snapshot (best for reading)
- `browser_take_screenshot()` - Take visual screenshot
- `browser_console_messages()` - Read console messages
- `browser_network_requests()` - See network requests

### Utilities
- `browser_wait_for(text, timeout)` - Wait for text to appear
- `browser_evaluate(function)` - Run JavaScript on page

## How to Run Browser Tests

### Prerequisites
1. **Backend must be running**: `cd apps/backend && uvicorn app.main:app --reload`
2. **Frontend must be running**: `cd apps/frontend && npm run dev`

### Test Scenarios

#### 1. Test Chat Interface Loading
```python
# I can navigate to http://localhost:3000/app/quote
# Check if chat interface loads
# Verify initial message appears
```

#### 2. Test Quote Flow
```python
# I can:
# - Type "I need a quote for Japan"
# - Click send button
# - Wait for response
# - Verify quote information appears
```

#### 3. Test Policy Questions
```python
# I can:
# - Type "What medical coverage do you provide?"
# - Click send
# - Verify policy response appears
```

#### 4. Test Error Handling
```python
# I can simulate errors and verify
# graceful error messages appear in UI
```

## Example: Testing Chat Enhancement 1 (LLM Intent Classification)

I can test that the new LLM intent classification works through the browser:

1. **Navigate** to chat page
2. **Type** "I need a quote" 
3. **Click** send
4. **Wait** for response
5. **Verify** response shows intent classification working (should route to quote flow)
6. **Check** backend console for "🎯 Intent Classification" logs

## Example: Testing Chat Enhancement 2 (Policy Explainer)

I can test the mock policy knowledge base:

1. **Navigate** to chat page
2. **Type** "What medical coverage do you provide?"
3. **Click** send
4. **Wait** for response
5. **Verify** response contains medical coverage details from mock KB
6. **Verify** response format matches Enhancement 2 requirements

## Running Tests

Just ask me to:
- "Test the chat interface in the browser"
- "Run browser tests for the enhancements"
- "Verify the quote flow works in the browser"
- "Test policy questions through the UI"

I'll use the browser automation tools directly to test your application!

## Current Status

✅ **Browser access available**
⚠️ **Requires servers running** (backend + frontend)
✅ **Can test all 4 enhancements through browser**
✅ **Can verify UI behavior matches backend changes**



