from __future__ import annotations

import json
import os
import tempfile

import firebase_admin
from firebase_admin import credentials, messaging


def init_firebase() -> None:
    """
    Inisialisasi Firebase Admin SDK dari service account JSON.
    Pastikan env var GOOGLE_APPLICATION_CREDENTIALS mengarah ke file JSON.
    """
    if firebase_admin._apps:
        return

    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not cred_path:
        raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        if raw:
            try:
                data = json.loads(raw)
            except Exception as e:
                raise RuntimeError(f"FIREBASE_SERVICE_ACCOUNT_JSON tidak valid JSON: {e}") from e

            fd, tmp_path = tempfile.mkstemp(prefix="firebase_", suffix=".json")
            os.close(fd)
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            cred_path = tmp_path
        else:
            raise RuntimeError(
                "Firebase credentials belum diset. "
                "Set GOOGLE_APPLICATION_CREDENTIALS (path file JSON) "
                "atau FIREBASE_SERVICE_ACCOUNT_JSON (isi JSON service account)."
            )

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)


def send_to_topic(
    topic: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
    notification: bool = True,
    android_priority: str = "high",
    sound: str | None = None,
) -> str:
    """
    Kirim push notification ke FCM topic (mis. 'sinabung').
    Return message_id jika sukses.
    """
    init_firebase()

    notif = None
    if notification:
        notif = messaging.Notification(
            title=title,
            body=body,
        )

    android_notification = None
    apns_cfg = None
    if sound:
        android_notification = messaging.AndroidNotification(sound=sound)
        apns_cfg = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound=sound),
            )
        )

    android_cfg = messaging.AndroidConfig(
        priority=android_priority,
        notification=android_notification,
    )

    msg = messaging.Message(
        topic=topic,
        notification=notif,
        data=data or {},
        android=android_cfg,
        apns=apns_cfg,
    )
    return messaging.send(msg)
