#!/usr/bin/env python3
"""
Google Calendar Meeting Notifier
Checks every 2 minutes for events starting now and displays 5 white notification frames
"""

import time
import tkinter as tk
from datetime import datetime, timedelta, UTC
from threading import Thread
import sys
import os.path
import argparse

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: Google Calendar API libraries not installed.")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Check interval in seconds (2 minutes)
CHECK_INTERVAL = 120

# Time window to check for events (check if event starts within next 2 minutes)
NOTIFICATION_WINDOW_MINUTES = 2

class CalendarNotifier:
    def __init__(self, calendar_id='primary', notify_keywords=None):
        self.creds = None
        self.service = None
        self.calendar_id = calendar_id
        self.notify_keywords = notify_keywords or []  # Keywords to trigger notifications (whitelist)
        self.active_events = {}  # Track active events with their end times: {event_id: end_datetime}
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        token_path = os.path.join(self.script_dir, 'token.json')
        creds_path = os.path.join(self.script_dir, 'credentials.json')
        
        # Load existing token
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If no valid credentials, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    print(f"Error: credentials.json not found in {self.script_dir}")
                    print("\nTo set up Google Calendar API:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a new project or select existing")
                    print("3. Enable Google Calendar API")
                    print("4. Create OAuth 2.0 credentials (Desktop app)")
                    print("5. Download credentials.json to this directory")
                    sys.exit(1)
                
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=self.creds)
        print("✓ Successfully authenticated with Google Calendar")

    def get_authenticated_user(self):
        """Get the authenticated user's email"""
        try:
            # The ID of primary calendar is the user's email
            calendar = self.service.calendars().get(calendarId='primary').execute()
            return calendar.get('id', 'Unknown')
        except HttpError as error:
            print(f'Error getting user info: {error}')
            return 'Unknown'

    def get_calendar_info(self, calendar_id):
        """Get calendar name and details"""
        try:
            calendar = self.service.calendars().get(calendarId=calendar_id).execute()
            return {
                'id': calendar.get('id', calendar_id),
                'summary': calendar.get('summary', 'Unknown Calendar'),
                'description': calendar.get('description', ''),
                'timezone': calendar.get('timeZone', 'UTC')
            }
        except HttpError as error:
            print(f'Error getting calendar info: {error}')
            return {
                'id': calendar_id,
                'summary': calendar_id,
                'description': '',
                'timezone': 'UTC'
            }

    def list_calendars(self):
        """List all available calendars"""
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])

            if not calendars:
                print('No calendars found.')
                return

            print("\n" + "=" * 80)
            print("Available Calendars:")
            print("=" * 80)

            for cal in calendars:
                cal_id = cal['id']
                summary = cal.get('summary', 'No name')
                access_role = cal.get('accessRole', 'unknown')
                primary = " [PRIMARY]" if cal.get('primary', False) else ""

                print(f"\nCalendar ID: {cal_id}{primary}")
                print(f"  Name: {summary}")
                print(f"  Access: {access_role}")
                if cal.get('description'):
                    print(f"  Description: {cal['description']}")

            print("\n" + "=" * 80)
            print("\nTo use a specific calendar, run:")
            print("  python calendar_notifier.py --calendar-id <CALENDAR_ID>")
            print("=" * 80 + "\n")

        except HttpError as error:
            print(f'An error occurred: {error}')

    def should_notify_event(self, event_title):
        """Check if event should trigger notification based on title keywords (whitelist)"""
        if not self.notify_keywords:
            # If no keywords specified, notify for all events
            return True

        # Case-insensitive matching - return True if ANY keyword matches
        title_lower = event_title.lower()
        for keyword in self.notify_keywords:
            if keyword.lower() in title_lower:
                return True
        # No keywords matched - skip this event
        return False

    def get_upcoming_events(self):
        """Get events starting within the notification window"""
        try:
            now = datetime.now(UTC)
            time_min = now.isoformat().replace('+00:00', 'Z')
            time_max = (now + timedelta(minutes=NOTIFICATION_WINDOW_MINUTES)).isoformat().replace('+00:00', 'Z')

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            return events

        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def show_notification_frames(self, event_title):
        """Display 5 white frames on top of all windows"""
        def create_frames():
            root = tk.Tk()
            root.withdraw()  # Hide main window

            # Get screen dimensions
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()

            frames = []
            frame_thickness = 50

            # Create 5 white overlay frames
            positions = [
                ('top', 0, 0, screen_width, frame_thickness),
                ('bottom', 0, screen_height - frame_thickness, screen_width, frame_thickness),
                ('left', 0, 0, frame_thickness, screen_height),
                ('right', screen_width - frame_thickness, 0, frame_thickness, screen_height),
                ('center', screen_width//2 - 200, screen_height//2 - 100, 400, 200)
            ]

            for name, x, y, width, height in positions:
                frame = tk.Toplevel(root)
                frame.overrideredirect(True)  # Remove window decorations

                # Multiple approaches to ensure window stays on top (Linux compatibility)
                frame.attributes('-topmost', True)

                # Try to set window type for X11 window managers
                try:
                    frame.attributes('-type', 'splash')  # Splash windows typically appear on top
                except:
                    pass

                frame.configure(bg='white')
                frame.geometry(f'{width}x{height}+{x}+{y}')

                # Add text to center frame
                if name == 'center':
                    label = tk.Label(
                        frame,
                        bg='white',
                        wraplength=350
                    )
                    label.pack(expand=True)

                frames.append(frame)

            # Force update to ensure windows are created
            root.update_idletasks()

            # Explicitly raise all frames to the top and grab focus
            for frame in frames:
                frame.lift()  # Raise window to top of stacking order
                frame.focus_force()  # Force focus to ensure visibility
                frame.attributes('-topmost', True)  # Re-assert topmost

            # Keep re-asserting topmost every 100ms to fight window managers
            def keep_on_top():
                for frame in frames:
                    try:
                        frame.lift()
                        frame.attributes('-topmost', True)
                    except:
                        pass

            # Re-assert at 100ms, 200ms, 300ms, etc.
            for delay in [100, 200, 300, 400, 500, 600, 700, 800, 900]:
                root.after(delay, keep_on_top)

            # Flash effect: destroy after 1 second
            root.after(1000, root.destroy)
            root.mainloop()
        
        # Run in separate thread to not block main loop
        thread = Thread(target=create_frames, daemon=True)
        thread.start()
    
    def check_calendar(self):
        """Check calendar for upcoming events"""
        current_time = datetime.now(UTC)
        
        # Clean up ended events from tracking
        ended_events = [
            event_id for event_id, end_time in self.active_events.items()
            if current_time > end_time
        ]
        for event_id in ended_events:
            del self.active_events[event_id]
            print(f"[{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}] ✓ Event ended: {event_id[:8]}...")
        
        # Get upcoming events
        events = self.get_upcoming_events()
        
        if not events:
            print(f"[{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}] No upcoming events")
            return
        
        for event in events:
            event_id = event['id']

            # Skip if this event is already active (we already notified)
            if event_id in self.active_events:
                continue

            # Get event details
            end = event['end'].get('dateTime', event['end'].get('date'))
            event_title = event.get('summary', 'Untitled Event')

            # Only notify for events containing specific keywords (whitelist)
            if not self.should_notify_event(event_title):
                print(f"[{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}] ⊘ Skipped (not in whitelist): {event_title}")
                continue
            
            # Parse end time
            try:
                if 'T' in end:  # DateTime format
                    end_datetime = datetime.fromisoformat(end.replace('Z', '+00:00')).replace(tzinfo=None)
                else:  # All-day event
                    end_datetime = datetime.fromisoformat(end) + timedelta(days=1)
            except:
                # Fallback: assume 1 hour event
                end_datetime = current_time + timedelta(hours=1)
            
            print(f"[{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}] 🔔 MEETING STARTING: {event_title}")
            print(f"    Event will end at: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            # Show notification frames
            self.show_notification_frames(event_title)
            
            # Mark event as active until it ends
            self.active_events[event_id] = end_datetime
    
    def run(self):
        """Main loop - check every 2 minutes"""
        # Get and display authenticated user and calendar info
        user_email = self.get_authenticated_user()
        calendar_info = self.get_calendar_info(self.calendar_id)

        print("=" * 80)
        print("Google Calendar Meeting Notifier")
        print("=" * 80)
        print(f"Authenticated User: {user_email}")
        print(f"Monitoring Calendar: {calendar_info['summary']}")
        print(f"  Calendar ID: {calendar_info['id']}")
        print(f"  Timezone: {calendar_info['timezone']}")
        if self.notify_keywords:
            print(f"Only notifying for events containing: {', '.join(repr(k) for k in self.notify_keywords)}")
        else:
            print("Notifying for all events")
        print("-" * 80)
        print(f"Checking every {CHECK_INTERVAL} seconds ({CHECK_INTERVAL//60} minutes)")
        print(f"Notification window: {NOTIFICATION_WINDOW_MINUTES} minutes before event")
        print("Press Ctrl+C to stop")
        print("=" * 80)
        
        try:
            while True:
                self.check_calendar()
                time.sleep(CHECK_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n\nStopping calendar notifier...")
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description='Google Calendar Meeting Notifier - Get notified when meetings start',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor with default whitelist (Triage, Rétro, Démo):
  python calendar_notifier.py

  # Monitor a specific calendar:
  python calendar_notifier.py --calendar-id your.email@gmail.com

  # Custom whitelist keywords:
  python calendar_notifier.py --notify "Standup" --notify "Review"

  # Notify for all events (no whitelist):
  python calendar_notifier.py --notify-all

  # List all available calendars:
  python calendar_notifier.py --list-calendars
        """
    )
    parser.add_argument(
        '--calendar-id',
        default='eqqpg4d73ni0c9essabco5v0k8@group.calendar.google.com',
        help='Calendar ID to monitor (default: eqqpg4d73ni0c9essabco5v0k8@group.calendar.google.com). Use --list-calendars to see available calendars.'
    )
    parser.add_argument(
        '--notify',
        action='append',
        dest='notify_keywords',
        help='Only notify for events containing this keyword (can be used multiple times). Case-insensitive.'
    )
    parser.add_argument(
        '--notify-all',
        action='store_true',
        help='Notify for all events (disable whitelist)'
    )
    parser.add_argument(
        '--list-calendars',
        action='store_true',
        help='List all available calendars and exit'
    )

    args = parser.parse_args()

    # Determine notify keywords (whitelist)
    if args.notify_all:
        notify_keywords = []
    elif args.notify_keywords:
        notify_keywords = args.notify_keywords
    else:
        # Default whitelist - only notify for these important meetings
        notify_keywords = ['Triage', 'Rétro', 'Démo']

    # Initialize notifier with specified calendar and whitelist
    notifier = CalendarNotifier(calendar_id=args.calendar_id, notify_keywords=notify_keywords)
    notifier.authenticate()

    # If --list-calendars is specified, list calendars and exit
    if args.list_calendars:
        notifier.list_calendars()
        sys.exit(0)

    # Otherwise, run the notifier
    notifier.run()

if __name__ == '__main__':
    main()
