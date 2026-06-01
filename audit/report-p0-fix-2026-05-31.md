# SURIOTA P0 SEO & Plugin Fix Report

Tanggal eksekusi: 31 Mei 2026, sekitar 09:22 WIB

## Ringkasan

Eksekusi P0 sudah dilakukan pada website live `https://suriota.com/` untuk masalah yang paling berdampak pada indexing, kualitas sitemap, metadata kritis, dan error browser.

Status akhir:

- AIOSEO sitemap sudah dipangkas agar taxonomy archive kosong tidak ikut dipublikasikan.
- Broken Tawk.to widget sudah dinonaktifkan.
- Referensi preconnect/dns-prefetch Tawk.to yang tidak lagi dipakai sudah dibersihkan.
- Metadata AIOSEO halaman penting bahasa Mandarin sudah diperbaiki.
- Error JavaScript `Unexpected token '|'` sudah diperbaiki.
- Redirect `www` masih perlu akses DNS/origin/Cloudflare karena tidak dapat diselesaikan dari WordPress REST.
- Sisa console warning/error berasal dari AdSense `no_div` pada beberapa halaman tanpa slot iklan; ini tidak lagi berupa page crash, tetapi perlu keputusan monetisasi sebelum diubah.

## Perubahan Yang Diterapkan

| Area | Status | Detail |
|---|---:|---|
| AIOSEO XML sitemap | Selesai | `category-sitemap.xml` dan `post_tag-sitemap.xml` tidak lagi masuk sitemap index. |
| AIOSEO HTML sitemap | Selesai | Taxonomy sitemap juga dipangkas dari konfigurasi HTML sitemap. |
| Tawk.to live chat | Selesai | Snippet `5549` diubah dari `publish` ke `draft` karena property/widget lama memicu CORS/runtime error. |
| Tawk preconnect | Selesai | Snippet `5550` dibersihkan dari `embed.tawk.to` dan `va.tawk.to`. |
| ZH AIOSEO metadata | Selesai | Title/description kritis diperbaiki untuk halaman ZH about dan 5 halaman pillar ZH. |
| JS language switcher | Selesai | Snippet `5599` diperbaiki dari regex rusak `^/+|/+$/g` menjadi escaped slash regex yang valid. |
| `www` redirect chain | Belum selesai | Masih multi-hop dan downgrade `https://www` ke `http://suriota.com`; butuh akses DNS/origin/Cloudflare. |

## Validasi Teknis

### Sitemap

Validasi live:

- `https://suriota.com/sitemap.xml`: `200`
- `page-sitemap.xml`: masih terdaftar
- `post-sitemap.xml`: masih terdaftar
- `category-sitemap.xml`: tidak lagi terdaftar, endpoint `404`
- `post_tag-sitemap.xml`: tidak lagi terdaftar, endpoint `404`

Konfigurasi AIOSEO tervalidasi:

- `options.sitemap.general.taxonomies.all = false`
- `options.sitemap.general.taxonomies.included = []`
- `options.sitemap.html.taxonomies.all = false`
- `options.sitemap.html.taxonomies.included = []`

### Browser Runtime

Playwright validation pada 7 sample page:

- Semua halaman sample return `200`.
- Semua halaman sample memiliki `1` H1.
- Schema utama masih muncul, termasuk `Organization`, `WebSite`, `WebPage`, `LocalBusiness`, dan schema khusus seperti `Service`, `FAQPage`, `ItemList`, atau `ContactPage` sesuai halaman.
- `pageErrors = 0` pada semua halaman sample setelah fix regex.
- Tawk runtime/CORS error sudah tidak muncul.

Sisa console:

- Beberapa halaman masih menunjukkan `Error: no_div` dari `pagead2.googlesyndication.com`.
- Ini terkait AdSense yang dimuat pada halaman tanpa slot iklan yang terdeteksi.
- Saya tidak mematikan AdSense karena snippet `5675` juga memuat GA4 + Consent Mode, dan perubahan monetisasi sebaiknya diputuskan eksplisit.

### Metadata ZH

Halaman yang diperbaiki:

- `/zh/guanyu-women/`
- `/zh/gongye-wulianwang-jicheng/`
- `/zh/ai-gongye-fenxi/`
- `/zh/shuzihua-zhuanxing-zixun/`
- `/zh/gongye-gongcheng-zidonghua/`
- `/zh/surge-saas-pingtai/`

Validasi live memastikan title/description sudah tidak corrupt dan canonical tetap mengarah ke URL masing-masing.

### Redirect

Kondisi akhir:

- `http://suriota.com/` -> `https://suriota.com/` -> `200`
- `https://www.suriota.com/` -> `http://suriota.com/` -> `https://suriota.com/` -> `200`
- `http://www.suriota.com/` -> `https://www.suriota.com/` -> `http://suriota.com/` -> `https://suriota.com/` -> `200`

Rekomendasi fix manual:

- Atur rule di Cloudflare/origin agar `https://www.suriota.com/*` langsung `301` ke `https://suriota.com/$1`.
- Atur `http://www.suriota.com/*` langsung `301` ke `https://suriota.com/$1`.
- Hindari hop ke `http://suriota.com/` dari HTTPS.

## Artifact & Backup

Backup dan hasil validasi:

- `backups/2026-05-31/p0-fix/pre-state.json`
- `backups/2026-05-31/p0-fix/apply-results.json`
- `backups/2026-05-31/p0-fix/post-validation.json`

Artifact audit browser:

- `tmp/suriota-browser-validate.json`
- `tmp/browser-audit/*.png`

Audit awal:

- `report.md`

## Status Akhir

P0 yang bisa dieksekusi dari akses WordPress/API sudah selesai dan tervalidasi. Sisa pekerjaan yang benar-benar masih terbuka adalah redirect `www` di layer DNS/origin/Cloudflare, plus keputusan apakah AdSense auto script perlu diubah agar hanya dimuat pada halaman yang memang memiliki slot iklan.
