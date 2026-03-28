# Google Calendar Integration - 3 Hour Execution Plan

## Goal
Integrate Google Calendar quickly so users can connect their account and view personal meetings in the app calendar.

## Target Scope for 3 Hours
- Google OAuth connect flow works end-to-end
- Fetch upcoming personal meetings from Google Calendar
- Show imported meetings in app calendar view
- Basic disconnect flow

## Timebox Summary
- Sprint length: 180 minutes
- Team split: 4 members
- Delivery strategy: ship Minimum Working Integration first, polish second

## Member Ownership

### Member 1 - Google Cloud + OAuth Setup
- Configure Google Cloud project
- Enable Calendar API
- Configure OAuth consent screen and test users
- Create OAuth client credentials
- Share environment values with team

### Member 2 - Backend OAuth + Google API
- Add backend endpoints for connect/callback/status/disconnect
- Implement token handling in memory for MVP
- Fetch Google Calendar events and normalize fields
- Expose merged calendar endpoint to frontend

### Member 3 - Frontend Integration
- Add Connect/Disconnect controls in calendar page
- Wire frontend service calls to new backend endpoints
- Render imported Google meetings with a source label
- Add loading/error states

### Member 4 - QA + Integration Support
- Smoke test flow continuously as features land
- Validate edge cases (empty calendar, revoked access, expired session)
- Help fix blockers quickly across frontend/backend
- Track launch checklist and final demo readiness

## Minute-by-Minute Plan

### 0-15 min: Kickoff and contracts
- Finalize endpoint contract and response shape
- Confirm minimal event schema:
  - id
  - title
  - dateTime
  - location
  - source (google/app)
- Assign owners and open dedicated branches

### 15-45 min: Parallel build round 1
- Member 1: finish OAuth credentials and test user setup
- Member 2: scaffold OAuth endpoints and callback handler
- Member 3: scaffold UI buttons and API methods
- Member 4: prepare test checklist and test accounts

### 45-90 min: Parallel build round 2
- Member 2: integrate Google events list call
- Member 2: expose merged calendar endpoint
- Member 3: integrate connect flow + calendar rendering
- Member 4: run first end-to-end tests and report issues

### 90-120 min: Integration and bug fixing
- Fix callback/redirect issues
- Fix CORS and session/token handling issues
- Ensure imported meetings appear in calendar view
- Add disconnect flow

### 120-150 min: Stabilization
- Handle common failures:
  - user denies consent
  - token expired
  - no meetings available
- Add minimal user feedback messages

### 150-170 min: Final verification
- Full happy-path demo run:
  - Connect
  - Fetch meetings
  - Display in calendar
  - Disconnect
- Quick code cleanup and config check

### 170-180 min: Handoff and demo prep
- Merge to main branch
- Update README with setup steps
- Capture demo script and known limitations

## API Contract (MVP)

### Backend endpoints
- GET /google/oauth/start
  - returns authUrl
- GET /google/oauth/callback
  - exchanges code and redirects to frontend
- GET /google/status
  - returns connected: true/false
- POST /google/disconnect
  - revokes/removes integration
- GET /calendar/{user_id}?include_google=true
  - returns merged app + google entries

## Success Criteria by Hour 3
- User can click Connect and complete OAuth
- Personal Google meetings are visible in calendar UI
- Disconnect works
- Team can demo full flow live

## If You Start Slipping (Scope Cut Plan)
1. Keep read-only sync only (no write-back to Google)
2. Keep in-memory token storage for demo only
3. Support only primary calendar
4. Skip recurring-event advanced handling if needed

## Post-3-Hour Follow-up (Next Iteration)
- Persist tokens securely in DB
- Add token refresh reliability
- Add background sync
- Add write-to-Google for club events
- Improve timezone and recurring event handling
