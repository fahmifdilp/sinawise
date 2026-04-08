# Deploy Gratis Awal: Supabase + Koyeb

Panduan ini menyiapkan backend FastAPI supaya online di internet, data disimpan di Postgres cloud, dan app Flutter bisa mengarah ke URL publik.

## Arsitektur

- Backend API: Koyeb
- Database: Supabase Postgres
- Push notification: Firebase Cloud Messaging
- App Android: build release dengan `API_BASE_URL` publik

## 1. Buat Database Supabase

1. Buat project baru di Supabase.
2. Setelah project jadi, di dashboard terbaru Supabase klik tombol `Connect` di bagian atas project.
3. Ambil connection string Postgres.
4. Default yang paling mudah untuk diisi adalah direct connection:

```env
DATABASE_URL=postgresql+psycopg://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
```

Catatan:
- Menurut docs Supabase, direct connection ideal untuk persistent server/container.
- Kalau host Anda nanti gagal konek karena keterbatasan IPv6, fallback ke `Session pooler` dari tombol `Connect`.
- Jangan pakai SQLite/file lokal kalau targetnya cloud multi-user.

## 2. Migrasikan Data Lokal ke Postgres

Dari folder backend:

```powershell
cd e:\Documents\sinawise\backend
$env:TARGET_DATABASE_URL="postgresql+psycopg://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require"
.\.venv\Scripts\python.exe scripts\migrate_local_to_postgres.py
```

Script ini memindahkan:
- tabel `Posko`
- tabel `Video`
- state JSON lama dari folder `data/`
- `state.json` lama ke key `scheduler_state`

## 3. Siapkan Firebase untuk Push Notification

1. Buka Firebase Console.
2. Buat service account baru.
3. Download JSON service account.
4. Simpan isi JSON itu untuk env:

```env
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
```

Di cloud lebih aman pakai `FIREBASE_SERVICE_ACCOUNT_JSON` daripada path file lokal.

## 4. Deploy Backend ke Koyeb

Repo ini sudah punya `Dockerfile` dan backend sekarang bisa jalan pakai `PORT` dari platform.

Di dashboard Koyeb:

1. `Create App`
2. Pilih repo GitHub proyek Anda
3. Root directory: `backend`
4. Build method: `Dockerfile`
5. Exposed port: `8000`
6. Health check path: `/health`

Set environment variables berikut:

```env
DATABASE_URL=postgresql+psycopg://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
LOG_LEVEL=info
ADMIN_USERNAME=sinauguardian@gmail.com
ADMIN_PASSWORD=ganti-password-admin
JWT_SECRET=ganti-jwt-secret
CORS_ALLOW_ORIGINS=*
FCM_TOPIC=sinabung
FCM_EMERGENCY_TOPIC=sinabung_emergency
MAGMA_TINGKAT_URL=https://magma.esdm.go.id/v1/gunung-api/tingkat-aktivitas
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
IOT_USE_MOCK=1
```

Setelah deploy berhasil, cek:

```text
https://NAMA-APP.koyeb.app/health
```

Harus mengembalikan `ok: true`.

## 5. Arahkan App Flutter ke URL Publik

Kalau URL backend Anda misalnya:

```text
https://sinawise-api.koyeb.app
```

Build app:

```powershell
cd e:\Documents\sinawise\sinabung_app
flutter build apk --flavor umkm01 --dart-define=API_BASE_URL=https://sinawise-api.koyeb.app
```

Atau install langsung ke HP:

```powershell
flutter run -d 10DD3Z08J4000CX --flavor umkm01 --dart-define=API_BASE_URL=https://sinawise-api.koyeb.app
```

Kalau backend sudah publik:
- tidak perlu `adb reverse`
- tidak perlu USB supaya user lain bisa pakai

## 6. Kalau Mau Dibagikan ke Banyak Orang

Pilihan termurah:

- Bagikan APK langsung via WhatsApp/Drive
- Atau upload ke GitHub Releases

Kalau mau resmi di Google Play:
- perlu akun Play Console
- ada biaya daftar satu kali

## 7. Batas Paket Gratis

Untuk tahap awal masih oke, tapi ada batas:

- Koyeb free akan scale-to-zero saat idle
- response pertama setelah tidur bisa lambat
- jangan anggap free tier sebagai production SLA

Kalau user mulai ramai, pindah ke paket berbayar kecil lebih aman.
