# User Monitoring Feature

**Date:** 2026-06-11  
**Status:** ✅ Completed and Tested

## Summary

Added comprehensive user account monitoring to the Tenable Health Check Agent. The new feature tracks user status, roles, login activity, and provides historical trends.

---

## Features Added

### 1. **User Account Tracking**
- Total user count (enabled vs disabled)
- New users created in the past 30 days
- Enabled users who haven't logged in for 30+ days
- User list with last login dates

### 2. **Role Distribution**
- Breakdown of users by role:
  - System Administrator (permission level 64)
  - Administrator (permission level 40)
  - Scan Manager (permission level 32)
  - Scan Operator (permission level 24)
  - Basic User (permission level 16)

### 3. **Login Activity Monitoring**
- Identifies enabled users with no login activity in 30+ days
- Shows users who have never logged in
- Useful for identifying stale accounts that should be disabled

### 4. **Historical Comparison**
- Tracks changes in user counts over time
- Shows 7-day and 30-day historical comparisons in HTML reports
- Trend data for long-term analysis

### 5. **Reporting**
- **Console Report:** Text-based summary with user tables
- **HTML Report:** Formatted tables with role breakdown and inactive user lists
- **Trends:** Historical charts showing user growth over time

---

## Technical Implementation

### New Files
- `src/collectors/user_collector.py` - Collects user data from Tenable API

### Modified Files
1. **src/tenable_client.py** - Added `list_users()` method
2. **src/main.py** - Integrated user collector into main flow
3. **src/analyzers/change_analyzer.py** - Added `analyze_users()` method
4. **src/reporters/console_reporter.py** - Added `print_users()` method
5. **src/reporters/html_reporter.py** - Added `_add_user_section()` method
6. **src/storage/trends_manager.py** - Added user metrics tracking
7. **src/generate_report.py** - Integrated user analysis
8. **README.md** - Updated feature list and sample output

---

## API Integration

Uses the official pytenable SDK methods:
- `tio.users.list()` - Retrieves all users with their attributes

### Data Retrieved
From each user object:
- `username` - User's login name
- `name` - Display name
- `email` - Email address
- `enabled` - Account status (true/false)
- `permissions` - Role/permission level (16, 24, 32, 40, 64)
- `created_at` - Account creation timestamp
- `last_login` - Last login timestamp (null if never logged in)

---

## Sample Output

### Console Report
```
USER ACCOUNTS
-------------
Total users: 8
Enabled users: 8
Disabled users: 0
New users (past 30 days): 0
Enabled users with no login in 30+ days: 8

--- User Roles ---
Role                    Count
--------------------  -------
Basic User                  3
System Administrator        2
Administrator               2
Unknown (0)                 1

--- Enabled Users - No Login in 30+ Days (Top 10) ---
Username                    Name              Last Login    Created
--------------------------  ----------------  ------------  ---------
user1@example.com           John Smith        Never         2025-01-15
user2@example.com           Jane Doe          2025-11-01    2024-03-20

Change from previous run:
  Total users: +2
  Enabled: +2
  Disabled: +0
  No login 30+ days: +1
```

### HTML Report
- Formatted table with current, 7-day, and 30-day historical data
- Role breakdown table sorted by count
- Inactive user table (top 10) with full details
- Responsive design matching Tenable branding

---

## Use Cases

### 1. **Security Audits**
Identify enabled accounts that haven't been used recently - potential security risk if compromised.

### 2. **License Optimization**
Find unused accounts to disable, potentially freeing up user licenses.

### 3. **User Onboarding Tracking**
Monitor new user creation over time.

### 4. **Access Reviews**
Regular review of who has which roles and permissions.

### 5. **Compliance**
Document user access patterns for compliance audits.

---

## Permissions Required

The API user running the health check must have **Administrator** or higher permissions to access the users endpoint. If insufficient permissions:
- The collector will log: "Users endpoint not available (may require Administrator permissions)"
- The report will show 0 users
- The rest of the health check continues normally

---

## Historical Trends

User metrics are now tracked in `data/trends.json`:
```json
{
  "users": [
    {
      "timestamp": "2026-06-11T18:35:54.729360+00:00",
      "total_users": 8,
      "enabled_users": 8,
      "disabled_users": 0,
      "new_users_30_days": 0,
      "enabled_no_login_30_days": 8
    }
  ]
}
```

This enables long-term tracking of:
- User account growth
- Disabled account trends
- Inactive user patterns
- New user onboarding velocity

---

## Configuration

No new configuration options required. The feature uses existing Tenable credentials and automatically collects user data on each run.

To disable user collection (if needed in the future), you could skip the collector in `main.py`.

---

## Testing Results

✅ Successfully collects user data from Tenable API  
✅ Correctly categorizes users by role/permission level  
✅ Identifies users with no recent login activity  
✅ Calculates 30-day new user count  
✅ Generates console report with user tables  
✅ Generates HTML report with formatted user section  
✅ Saves user trends for historical tracking  
✅ Handles missing permissions gracefully  
✅ All Python files compile without errors  

---

## Future Enhancements

Possible improvements for future versions:
1. **MFA Status** - Track which users have MFA enabled
2. **Last Login Threshold** - Configurable threshold (currently 30 days)
3. **Email Alerts** - Notify admins of stale accounts
4. **CSV Export** - Export user list to spreadsheet
5. **Group Membership** - Track user group assignments
6. **Permission Changes** - Alert on role/permission changes
7. **API Key Tracking** - Monitor API keys owned by users

---

## Files Modified Summary

| File | Lines Added | Purpose |
|------|-------------|---------|
| `src/collectors/user_collector.py` | +109 | New collector for user data |
| `src/tenable_client.py` | +18 | Added list_users() method |
| `src/main.py` | +5 | Integrated user collector |
| `src/analyzers/change_analyzer.py` | +27 | User change analysis |
| `src/reporters/console_reporter.py` | +36 | Console user reporting |
| `src/reporters/html_reporter.py` | +134 | HTML user section |
| `src/storage/trends_manager.py` | +13 | User trend tracking |
| `src/generate_report.py` | +1 | User analysis in reports |
| `README.md` | +19 | Documentation updates |

**Total:** ~362 lines added across 9 files

---

## Backward Compatibility

✅ **Fully backward compatible** - existing health check data files and reports continue to work without modification.

If the user endpoint is unavailable:
- Logs informational message
- Returns empty user data
- Rest of health check proceeds normally

Older data files without user data:
- Analysis gracefully handles missing user sections
- Reports show "First run - no previous data" for user comparison

---

**Completed by:** Claude Code  
**Tested on:** Tenable Cloud Platform  
**Review Status:** Ready for commit
