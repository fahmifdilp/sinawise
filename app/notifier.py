from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Optional

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger("sinabung.notifier")


def _ensure_cred_file() -> str:
    """
    Mendapatkan path kredensial Firebase Admin.
    Pilihan:
    1) GOOGLE_APPLICATION_CREDENTIALS=/path/serviceAccount.json
    2) FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account", ...}'  (disarankan di Railway)
    """
    # 1) Path langsung
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if cred_path:
        return cred_path

    # 2) JSON dari env
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if raw:
        try:
            data = json.loads(raw)
        except Exception as e:
            raise RuntimeError(f"FIREBASE_SERVICE_ACCOUNT_JSON tidak valid JSON: {e}") from e

        # tulis ke file temp
        fd, tmp_path = tempfile.mkstemp(prefix="firebase_", suffix=".json")
        os.close(fd)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return tmp_path

    raise RuntimeError(
        "Firebase credentials belum diset. "
        "Set GOOGLE_APPLICATION_CREDENTIALS (path file JSON) "
        "atau FIREBASE_SERVICE_ACCOUNT_JSON (isi JSON service account)."
    )


def init_firebase() -> None:
    """
    Inisialisasi Firebase Admin SDK.
    """
    if firebase_admin._apps:
        return

    cred_path = _ensure_cred_file()
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin initialized. cred=%s", cred_path)


def send_to_topic(
    topic: str,
    title: str,
    body: str,
    data: Optional[dict[str, str]] = None,
    *,
    android_channel_id: Optional[str] = None,
    android_sound: Optional[str] = "default",
    high_priority: bool = True,
    ttl_seconds: int = 3600,
) -> str:
    """
    Kirim FCM ke topic dengan Notification + Data.
    Cocok untuk banner notifikasi sistem.
    Catatan: di Android, 'notification message' kadang tidak memanggil background handler.
    """
    init_firebase()

    channel_id = android_channel_id or os.getenv("FCM_ANDROID_CHANNEL_ID", "sinawise_alerts")

    android_cfg = messaging.AndroidConfig(
        priority="high" if high_priority else "normal",
        ttl=ttl_seconds,
        notification=messaging.AndroidNotification(
            channel_id=channel_id,
            sound=android_sound or None,
            click_action="FLUTTER_NOTIFICATION_CLICK",
        ),
    )

    apns_cfg = messaging.APNSConfig(
        headers={"apns-priority": "10" if high_priority else "5"},
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                sound=android_sound or None,
                content_available=True,
            )
        ),
    )

    msg = messaging.Message(
        topic=topic,
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        android=android_cfg,
        apns=apns_cfg,
    )

    logger.info("FCM SEND (notif+data) topic=%s title=%s data=%s", topic, title, data or {})
    return messaging.send(msg)


def send_to_topic_data(
    topic: str,
    data: dict[str, str],
    *,
    high_priority: bool = True,
    ttl_seconds: int = 3600,
) -> str:
    """
    Kirim FCM DATA-ONLY (tanpa field notification).
    Ini yang paling aman untuk memicu FirebaseMessaging.onBackgroundMessage di Flutter.

    Flutter-lah yang akan:
    - tampilkan local notification (flutter_local_notifications)
    - mainkan bunyi/alarm (audioplayers)
    - bisa tampilkan full-screen page jika app dibuka
    """
    init_firebase()

    android_cfg = messaging.AndroidConfig(
        priority="high" if high_priority else "normal",
        ttl=ttl_seconds,
    )

    apns_cfg = messaging.APNSConfig(
        headers={"apns-priority": "10" if high_priority else "5"},
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                content_available=True,
            )
        ),
    )

    msg = messaging.Message(
        topic=topic,
        data=data,
        android=android_cfg,
        apns=apns_cfg,
    )

    logger.info("FCM SEND (data-only) topic=%s data=%s", topic, data)
    return messaging.send(msg)
