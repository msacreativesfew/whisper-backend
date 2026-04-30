import base64
import datetime
import os
from email.message import EmailMessage

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from livekit.agents import llm as lk_llm


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/fitness.activity.read",
]

TOKEN_PATH = "token.json"


def get_google_credentials(scopes: list[str] | None = None) -> Credentials:
    scopes = scopes or SCOPES
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)
    elif os.getenv("GOOGLE_TOKEN_JSON"):
        import json
        try:
            token_info = json.loads(os.getenv("GOOGLE_TOKEN_JSON"))
            creds = Credentials.from_authorized_user_info(token_info, scopes)
        except Exception as e:
            print(f"Error loading GOOGLE_TOKEN_JSON: {e}")

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None

    if creds and not creds.has_scopes(scopes):
        creds = None

    if not creds or not creds.valid:
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

        if os.path.exists(credentials_path):
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0, include_granted_scopes=True)
            with open(TOKEN_PATH, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
        elif creds_json:
            import json
            try:
                info = json.loads(creds_json)
                flow = InstalledAppFlow.from_client_config(info, scopes)
                # On server, we can't run_local_server. We expect a token.json to exist
                # or for the user to provide a refresh token.
                # However, for now we will just raise a more helpful error if token.json is missing.
                if not creds:
                    raise RuntimeError(
                        "Google token.json not found on server. "
                        "Please run locally first to generate token.json or provide a full refresh token."
                    )
            except Exception as e:
                raise RuntimeError(f"Failed to load GOOGLE_CREDENTIALS_JSON: {e}")
        else:
            raise FileNotFoundError(
                f"Credentials file not found at {credentials_path} and GOOGLE_CREDENTIALS_JSON env var is missing."
            )

    return creds


def get_gmail_service():
    return build("gmail", "v1", credentials=get_google_credentials(), cache_discovery=False)


def get_calendar_service():
    return build("calendar", "v3", credentials=get_google_credentials(), cache_discovery=False)


def get_drive_service():
    return build("drive", "v3", credentials=get_google_credentials(), cache_discovery=False)


def get_fitness_service():
    return build("fitness", "v1", credentials=get_google_credentials(), cache_discovery=False)


def _get_google_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not configured.")
    return api_key


def _header_value(headers: list[dict], name: str, default: str = "") -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", default)
    return default


def _extract_text_from_payload(payload: dict | None) -> str:
    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")
    if mime_type == "text/plain" and body_data:
        try:
            return base64.urlsafe_b64decode(body_data.encode("utf-8")).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    for part in payload.get("parts", []) or []:
        text = _extract_text_from_payload(part)
        if text:
            return text
    return ""


def _parse_google_duration_seconds(value: str | None) -> int:
    if not value or not value.endswith("s"):
        return 0
    try:
        return int(float(value[:-1]))
    except ValueError:
        return 0


def _format_seconds(total_seconds: int) -> str:
    if total_seconds <= 0:
        return "0 min"
    minutes = total_seconds // 60
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes} min"


def _traffic_level(actual_seconds: int, free_flow_seconds: int) -> str:
    if actual_seconds <= 0 or free_flow_seconds <= 0:
        return "unknown"

    ratio = actual_seconds / max(1, free_flow_seconds)
    if ratio <= 1.1:
        return "free flowing"
    if ratio <= 1.35:
        return "moderate traffic"
    if ratio <= 1.65:
        return "busy traffic"
    return "heavy traffic"


async def _geocode_address(address: str) -> dict:
    api_key = _get_google_api_key()
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": api_key},
        )
        data = response.json()

    results = data.get("results", [])
    if not results:
        raise ValueError(f"Could not find location for '{address}'.")

    first = results[0]
    location = first["geometry"]["location"]
    return {
        "address": first.get("formatted_address", address),
        "lat": location["lat"],
        "lng": location["lng"],
    }


async def _weather_for_coordinates(lat: float, lon: float, label: str) -> str:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m",
                "timezone": "auto",
            },
        )
        weather = response.json()["current"]

    codes = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "foggy",
        48: "icy fog",
        51: "light drizzle",
        53: "drizzle",
        61: "light rain",
        63: "rain",
        65: "heavy rain",
        71: "light snow",
        73: "snow",
        75: "heavy snow",
        80: "rain showers",
        81: "showers",
        82: "heavy showers",
        95: "thunderstorm",
        96: "thunderstorm with hail",
        99: "heavy thunderstorm",
    }

    return (
        f"Weather near {label}: {codes.get(weather['weather_code'], 'mixed conditions')}, "
        f"{weather['temperature_2m']} C, humidity {weather['relative_humidity_2m']}%, "
        f"wind {weather['wind_speed_10m']} km/h."
    )


@lk_llm.function_tool
async def read_emails(count: int = 5, query: str = "is:unread in:inbox") -> str:
    """Read recent Gmail messages. Returns message ids, senders, subjects, and snippets."""
    try:
        service = get_gmail_service()
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max(1, min(count, 10)))
            .execute()
        )
        messages = results.get("messages", [])

        if not messages:
            return "No matching emails were found."

        lines = ["Recent emails:"]
        for msg in messages:
            msg_data = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                )
                .execute()
            )
            headers = msg_data.get("payload", {}).get("headers", [])
            subject = _header_value(headers, "Subject", "No Subject")
            sender = _header_value(headers, "From", "Unknown Sender")
            date = _header_value(headers, "Date", "Unknown Date")
            snippet = msg_data.get("snippet", "")
            lines.append(
                f"- id={msg['id']} | From: {sender} | Subject: {subject} | Date: {date} | Snippet: {snippet}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to read emails: {e}"


@lk_llm.function_tool
async def read_email_detail(message_id: str) -> str:
    """Read the full plain-text body of a Gmail message by its message id."""
    try:
        service = get_gmail_service()
        msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        headers = msg.get("payload", {}).get("headers", [])
        subject = _header_value(headers, "Subject", "No Subject")
        sender = _header_value(headers, "From", "Unknown Sender")
        body = _extract_text_from_payload(msg.get("payload")) or msg.get("snippet", "No message body found.")
        return f"Email from {sender}\nSubject: {subject}\nBody:\n{body[:4000]}"
    except Exception as e:
        return f"Failed to read email detail: {e}"


@lk_llm.function_tool
async def send_email(to: str, subject: str, body: str) -> str:
    """Send an email from Gmail."""
    try:
        service = get_gmail_service()
        message = EmailMessage()
        message.set_content(body)
        message["To"] = to
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        service.users().messages().send(userId="me", body={"raw": encoded_message}).execute()
        return f"Email sent to {to}."
    except Exception as e:
        return f"Failed to send email: {e}"


@lk_llm.function_tool
async def update_email_labels(
    message_id: str,
    mark_read: bool = False,
    mark_unread: bool = False,
    archive: bool = False,
    star: bool = False,
    unstar: bool = False,
) -> str:
    """Modify a Gmail message by marking read or unread, archiving, or starring it."""
    try:
        add_labels: list[str] = []
        remove_labels: list[str] = []

        if mark_read:
            remove_labels.append("UNREAD")
        if mark_unread:
            add_labels.append("UNREAD")
        if archive:
            remove_labels.append("INBOX")
        if star:
            add_labels.append("STARRED")
        if unstar:
            remove_labels.append("STARRED")

        service = get_gmail_service()
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": add_labels, "removeLabelIds": remove_labels},
        ).execute()
        return f"Email {message_id} was updated successfully."
    except Exception as e:
        return f"Failed to modify email: {e}"


@lk_llm.function_tool
async def delete_email(message_id: str, permanently_delete: bool = False) -> str:
    """Delete a Gmail message by moving it to trash or deleting it permanently."""
    try:
        service = get_gmail_service()
        if permanently_delete:
            service.users().messages().delete(userId="me", id=message_id).execute()
            return f"Email {message_id} was permanently deleted."

        service.users().messages().trash(userId="me", id=message_id).execute()
        return f"Email {message_id} was moved to trash."
    except Exception as e:
        return f"Failed to delete email: {e}"


@lk_llm.function_tool
async def get_calendar_events(days: int = 1) -> str:
    """Get upcoming Google Calendar events for the next given number of days."""
    try:
        service = get_calendar_service()
        now = datetime.datetime.now(datetime.timezone.utc)
        end = now + datetime.timedelta(days=max(1, min(days, 14)))

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            return "No upcoming calendar events were found."

        lines = ["Upcoming calendar events:"]
        for event in events:
            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "Unknown"))
            summary = event.get("summary", "Untitled event")
            event_id = event.get("id", "")
            lines.append(f"- id={event_id} | {summary} | starts {start}")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to retrieve calendar events: {e}"


@lk_llm.function_tool
async def add_calendar_event(summary: str, start_time: str, end_time: str, description: str = "") -> str:
    """Add an event to Google Calendar using ISO datetime strings."""
    try:
        service = get_calendar_service()
        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"Event created with id {created.get('id')}."
    except Exception as e:
        return f"Failed to create event: {e}"


@lk_llm.function_tool
async def list_drive_files(query: str = "", count: int = 10) -> str:
    """List or search Google Drive files."""
    try:
        service = get_drive_service()
        clauses = ["trashed = false"]
        if query.strip():
            safe_query = query.replace("'", "\\'")
            clauses.append(
                f"(name contains '{safe_query}' or fullText contains '{safe_query}')"
            )

        result = (
            service.files()
            .list(
                q=" and ".join(clauses),
                pageSize=max(1, min(count, 20)),
                fields="files(id,name,mimeType,modifiedTime,webViewLink)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )
        files = result.get("files", [])
        if not files:
            return "No matching Drive files were found."

        lines = ["Drive files:"]
        for item in files:
            lines.append(
                f"- id={item.get('id')} | {item.get('name')} | {item.get('mimeType')} | "
                f"modified {item.get('modifiedTime')} | {item.get('webViewLink', 'no link')}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to read Drive files: {e}"


@lk_llm.function_tool
async def get_fitness_summary(days: int = 1) -> str:
    """Get Google Fitness activity totals like steps and calories for recent days."""
    try:
        service = get_fitness_service()
        end = datetime.datetime.now(datetime.timezone.utc)
        start = end - datetime.timedelta(days=max(1, min(days, 30)))

        body = {
            "aggregateBy": [
                {"dataTypeName": "com.google.step_count.delta"},
                {"dataTypeName": "com.google.calories.expended"},
            ],
            "bucketByTime": {"durationMillis": max(1, days) * 24 * 60 * 60 * 1000},
            "startTimeMillis": int(start.timestamp() * 1000),
            "endTimeMillis": int(end.timestamp() * 1000),
        }

        result = service.users().dataset().aggregate(userId="me", body=body).execute()
        steps = 0
        calories = 0.0

        for bucket in result.get("bucket", []):
            for dataset in bucket.get("dataset", []):
                data_source = dataset.get("dataSourceId", "")
                for point in dataset.get("point", []):
                    for value in point.get("value", []):
                        if "step_count" in data_source:
                            steps += int(value.get("intVal", 0))
                        elif "calories" in data_source:
                            calories += float(value.get("fpVal", 0.0))

        return (
            f"Google Fitness summary for the last {max(1, days)} day(s): "
            f"{steps} steps and about {round(calories, 1)} calories."
        )
    except Exception as e:
        return f"Failed to read fitness data: {e}"


@lk_llm.function_tool
async def get_route_brief(origin: str, destination: str, travel_mode: str = "DRIVE") -> str:
    """Get a route summary with traffic conditions and destination weather."""
    try:
        api_key = _get_google_api_key()
        origin_geo, destination_geo = await _geocode_address(origin), await _geocode_address(destination)

        body = {
            "origin": {
                "location": {
                    "latLng": {"latitude": origin_geo["lat"], "longitude": origin_geo["lng"]}
                }
            },
            "destination": {
                "location": {
                    "latLng": {"latitude": destination_geo["lat"], "longitude": destination_geo["lng"]}
                }
            },
            "travelMode": travel_mode.upper(),
            "routingPreference": "TRAFFIC_AWARE",
            "languageCode": "en-US",
            "units": "METRIC",
        }

        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "routes.duration,routes.staticDuration,routes.distanceMeters,routes.localizedValues",
        }

        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                "https://routes.googleapis.com/directions/v2:computeRoutes",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            route_data = response.json()

        routes = route_data.get("routes", [])
        if not routes:
            return "No route was found."

        route = routes[0]
        traffic_seconds = _parse_google_duration_seconds(route.get("duration"))
        free_seconds = _parse_google_duration_seconds(route.get("staticDuration"))
        distance_km = round(route.get("distanceMeters", 0) / 1000, 1)
        traffic_label = _traffic_level(traffic_seconds, free_seconds)
        delay_minutes = max(0, round((traffic_seconds - free_seconds) / 60))
        weather = await _weather_for_coordinates(
            destination_geo["lat"], destination_geo["lng"], destination_geo["address"]
        )

        return (
            f"Route from {origin_geo['address']} to {destination_geo['address']}: "
            f"{distance_km} km, ETA {_format_seconds(traffic_seconds)}, normal drive {_format_seconds(free_seconds)}. "
            f"Roads look {traffic_label}"
            f"{f' with about {delay_minutes} extra min from traffic.' if delay_minutes else '.'} "
            f"{weather}"
        )
    except Exception as e:
        return f"Failed to get route details: {e}"
