# Gopesh & Prachi Wedding RSVP — prototype

A small Flask + SQLite prototype for event-by-event wedding RSVPs, playful party-style selections, companion counts, duplicate prevention by mobile number, suggested friend matches, sender-tagged share links, a private admin dashboard, and CSV export.

## Important prototype limitations
- This is a prototype, not a production-hardened wedding service.
- SQLite is fine for local testing. For a hosted version, use a persistent disk or migrate to managed PostgreSQL/Supabase before relying on it for live guest responses.
- Set a strong admin password and secret key before hosting.
- Names are prefilled only if you add that feature; this build intentionally asks guests to enter their own names because you do not want to pre-enter a guest list.
- The web browser cannot automatically read a guest's WhatsApp profile name or phone number.
- Companion names are suggestions, not identity proof. The dashboard does not automatically subtract possible overlaps; review them manually.
- Share links tag the sender and permitted total party size, but anyone can forward a link. For strict per-household limits, create distinct invitation tokens or add OTP verification before launch.
- A declared +1 is counted as an additional person. If that person also RSVPs independently, the admin must resolve the suggested match to avoid duplicate headcounts. This MVP deliberately avoids auto-merging based on names alone.
- Before public launch, add rate limiting, CSRF protection, secure cookie settings, backup/retention controls, and a production database.

## Run locally

Python 3.10+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export RSVP_ADMIN_PASSWORD='use-a-long-unique-password'
export RSVP_SECRET_KEY='use-a-long-random-secret'
export RSVP_PUBLIC_BASE_URL='http://127.0.0.1:5000'
python app.py
```

Open:
- Guest RSVP: http://127.0.0.1:5000/
- Admin dashboard: http://127.0.0.1:5000/admin

In the admin dashboard, choose **Create share link**. Make a sender-tagged link for each person sending invitations, then copy it into WhatsApp. The `max` value is total people including the invitee. Keep a link's audience within that limit.

## Hosting checklist
1. Choose a host that supports Python/Flask and persistent data, or switch SQLite to Supabase/PostgreSQL.
2. Set `RSVP_ADMIN_PASSWORD`, `RSVP_SECRET_KEY`, and `RSVP_PUBLIC_BASE_URL` in host environment variables.
3. Configure HTTPS and verify the app's cookie/security settings.
4. Test guest RSVP, edits by the same phone, admin login, CSV export, and companion overlap cases.
5. Export and back up responses regularly.

## Latest UX update
The RSVP form now asks guests to choose a playful party vibe: family, better half, solo/open to a plot twist, or solo just here to celebrate. Companion count/name fields appear only for family or better-half options. Existing SQLite databases are migrated automatically to add the party-vibe field.


## Mobile number validation (v9)
- The mobile field requests a numeric keypad on supported phones.
- The browser removes non-digit characters but does not impose a 10-digit limit, so international numbers and country codes are supported.
- The server independently requires at least one digit and stores the digit-only number for duplicate detection.
