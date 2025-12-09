# Message Interactions - Visual Guide

## Desktop Experience

### Right-Click Context Menu
```
┌─────────────────────┐
│ ✓ Select            │  <- Toggle message selection
│ ℹ️ Info              │  <- Show message info (time, read status, user status)
│ 📌 Pin              │  <- Pin message (placeholder)
│ ➤ Forward           │  <- Forward with "[Forwarded]:" prefix
├─────────────────────┤
│ 🗑️ Delete           │  <- Delete (own messages only)
└─────────────────────┘
```

### Message Layout
```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  [Reply Icon]  ┌─────────────────────────────────────────┐   │
│     (👈)       │  Replying to: Original message text...  │   │
│                │  ────────────────────────────────────   │   │
│                │  My actual message content here         │   │
│                │                                2:30 PM ✓✓│   │
│                └─────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Reply Icon** (Desktop Only)
- Position: Fixed beside message (left or right)
- Visibility: On message hover
- Action: Sets reply context for next message

---

## Mobile Experience

### Long-Press Menu (500ms Hold)
```
When user holds message for 500ms:

┌──────────────────────┐
│  ✓ Select            │
│  ℹ️ Info              │
│  📌 Pin              │
│  ➤ Forward           │
│  🗑️ Delete           │  (own messages only)
└──────────────────────┘
```

**Menu Positioning**: Bottom-center of screen (above keyboard)

### Simplified Info Display
```
┌─────────────────────────┐
│   Message Info          │
├─────────────────────────┤
│ 🕐 Sent      2:30 PM    │
├─────────────────────────┤
│ ✓✓ Read      Read       │
│   (or "Not Read")       │
├─────────────────────────┤
│ 🟢 Status    Online      │
│   (or "Offline")        │
├─────────────────────────┤
│        [Close]          │
└─────────────────────────┘
```

### Swipe-Left Reply Gesture
```
Message is swiped from left edge:

👈 [Reply Icon Appears]

└─> Gesture triggers reply action
```

---

## Info Display Details

### What Shows in Info Box

| Element | Value | Color |
|---------|-------|-------|
| 🕐 Sent Time | Extracted from timestamp (e.g., "2:30 PM") | Gray |
| ✓✓ Read Status | "Read" if message is read, "Not Read" if not | Green/Gray |
| 🟢 User Status | "Online" or "Offline" (shows online status) | Green/Gray |

**Example 1 - Message Read by Recipient:**
```
🕐 Sent        2:30 PM
✓✓ Read        Read
🟢 Status      Online
```

**Example 2 - Message Not Yet Read:**
```
🕐 Sent        3:45 PM
✓✓ Read        Not Read
🟢 Status      Offline
```

---

## Message Actions Behavior

### Select Multiple
- Click "Select" in menu
- Message gets ring highlight: `ring-2 ring-indigo-500`
- Multiple messages can be selected
- Future: Bulk delete/forward implementation

### Forward Message
- Copies message text
- Prepends: `[Forwarded]: `
- Sends as new message
- Shows: ✓ Message forwarded (green toast)

### Delete Message
1. Click "Delete" in menu
2. Confirmation dialog appears: "Are you sure you want to delete this message?"
3. If confirmed:
   - Message text becomes: `[Message deleted]`
   - Message opacity: 50%
   - Shows: ✓ Message deleted (red toast)
   - **Only sender can delete** (delete button hidden for others)

### Pin Message
- Click "Pin" in menu
- Shows: ✓ Message pinned (green toast)
- **Future**: Pinned messages appear at chat top

---

## Responsive Behavior

### Desktop (≥768px, md breakpoint)
```
✅ Right-click context menu
✅ Reply icon visible beside messages
✅ Full menu options (Select, Info, Pin, Forward, Delete)
✅ No touch handlers active
✅ Hover effects visible
```

### Mobile (<768px)
```
✅ Long-press (500ms) triggers menu
✅ Menu positioned bottom-center
✅ Reply icon hidden (use swipe-left gesture instead)
✅ Touch-optimized button sizes
✅ Simplified UI
❌ Hover effects not applicable
```

---

## User Interaction Flow

### Desktop: Send + Reply
```
1. User types message
2. Clicks send button (arrow icon)
3. Message appears in chat
4. To reply:
   - Hover over message
   - Click reply icon (👈) beside message
   - Reply bar appears: "Replying to: <text>"
   - Type reply
   - Send (reply linked in DB)
```

### Mobile: Send + Reply (via swipe)
```
1. User types message
2. Clicks send button
3. Message appears in chat
4. To reply:
   - Swipe message left
   - Reply action triggered
   - Reply bar appears
   - Type reply
   - Send
```

### Desktop: Delete Message
```
1. Hover over own message
2. Right-click on message
3. Context menu appears
4. Click "Delete"
5. Confirmation: "Are you sure?"
6. If YES:
   - Message shows "[Message deleted]"
   - Toast: ✓ Message deleted
```

### Mobile: Delete Message
```
1. Long-press message (500ms)
2. Menu appears at bottom
3. Tap "Delete" (red, at bottom)
4. Confirmation dialog
5. If OK:
   - Message shows "[Message deleted]"
   - Toast: ✓ Message deleted
```

---

## CSS Classes Used

| Class | Purpose |
|-------|---------|
| `message-item` | Container div for each message |
| `hidden md:flex` | Reply icon: hidden on mobile, visible on desktop |
| `md:hidden` | Swipe hint: hidden on desktop, visible on mobile |
| `group` | Enables group-hover effects |
| `ring-2 ring-indigo-500` | Visual highlight for selected messages |
| `animate-fade-in` | Toast notification fade-in effect |
| `animate-slide-up` | Mobile menu slide-up effect |

---

## Data Attributes

```html
<div class="message-item" 
     id="msg-{{ message.id }}"
     data-message-id="{{ message.id }}"
     data-message-text="{{ message.text|escapejs }}"
     oncontextmenu="showContextMenu(...)"
     ontouchstart="startLongPress(...)"
     ontouchend="cancelLongPress()">
```

- `id`: Used for DOM selection and scrolling
- `data-message-id`: Message UUID for tracking
- `data-message-text`: Safe text extraction (escaped)
- Event handlers: Right-click, long-press, touch-end

---

## Toast Notifications

### Success (Green)
```
┌──────────────────────────────┐
│ ✓ Message forwarded          │
└──────────────────────────────┘
Auto-dismisses after 2 seconds
```

### Delete (Red)
```
┌──────────────────────────────┐
│ ✓ Message deleted            │
└──────────────────────────────┘
Auto-dismisses after 2 seconds
```

---

## Implementation Summary

| Feature | Desktop | Mobile |
|---------|---------|--------|
| **Context Menu** | Right-click | Long-press (500ms) |
| **Reply** | Icon button | Swipe-left |
| **Info Display** | Same as mobile | Simplified (time, read, status) |
| **Delete Confirmation** | Browser dialog | Browser dialog |
| **Menu Position** | At cursor | Bottom-center |
| **Own Message Indicator** | Delete button visible | Delete button visible |

---

## Next Steps / TODOs

- [ ] Implement actual swipe-left detection
- [ ] Add real-time user online/offline status
- [ ] Implement pin message display
- [ ] Add bulk operations with selected messages
- [ ] Add edit message functionality
- [ ] Add emoji reactions
- [ ] Add message search
- [ ] Add message export

