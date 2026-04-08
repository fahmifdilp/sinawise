# sinawise

## Deploy cloud

Panduan deploy backend ke Supabase + Koyeb ada di:

- `DEPLOY_KOYEB_SUPABASE.md`

## MAGMA hourly updater (GitHub Actions)

Jika backend cloud Anda tidak bisa akses MAGMA langsung, gunakan updater per jam ini.

1. Buka GitHub repo -> Settings -> Secrets and variables -> Actions.
2. Tambah repository secrets:
   - `BACKEND_URL` contoh: `https://sinawise-api.koyeb.app`
   - `ADMIN_USERNAME`
   - `ADMIN_PASSWORD`
   - `MAGMA_TINGKAT_URL` (opsional): `https://magma.esdm.go.id/v1/gunung-api/tingkat-aktivitas`
3. Workflow `Update MAGMA Cache Hourly` akan jalan tiap 1 jam.
4. Bisa jalankan manual dari tab Actions (`workflow_dispatch`).
