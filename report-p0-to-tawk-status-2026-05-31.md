# SURIOTA P0 Execution, Tawk Restore Attempt, and Current Status Report

Tanggal: 31 Mei 2026  
Scope: audit SEO teknis, eksekusi P0, validasi pasca-fix, dan tindak lanjut Tawk.to.

## Executive Summary

Audit awal menemukan beberapa isu P0/P1 pada sitemap, metadata ZH, runtime JavaScript, dan Tawk.to. P0 yang dapat dieksekusi dari akses WordPress REST sudah selesai dan tervalidasi.

Setelah itu ada request tambahan untuk mengaktifkan kembali Tawk.to. Direct chat button berhasil dipasang tanpa error, tetapi user mengklarifikasi bahwa yang dibutuhkan adalah embedded Tawk untuk visitor monitoring. Beberapa pendekatan embed diuji, namun loader Tawk resmi saat ini terblokir di Chromium karena kombinasi `application/x-javascript`, `nosniff`, `crossorigin`, ORB, dan request internal ke `va.tawk.to` yang CORS-nya tidak mengizinkan origin `suriota.com` pada beberapa endpoint.

Saat mencoba opsi server-side proxy via plugin snippet PHP, plugin `Code Snippets` yang baru dipasang mengaktifkan snippet lama dari database plugin tersebut dan sempat menyebabkan fatal error. Kondisi terakhir sudah pulih: homepage, `/contact/`, dan `/wp-json` kembali `200`; plugin Code Snippets sekarang inactive dengan path `code-snippets-test/code-snippets`.

## Kondisi Terakhir

Status live terakhir:

- `https://suriota.com/`: `200`
- `https://suriota.com/contact/`: `200`
- `https://suriota.com/wp-json`: `200`
- `Tawk.to Live Chat` plugin: active, versi `0.9.3`
- `Code Snippets`: inactive, terdeteksi sebagai `code-snippets-test/code-snippets`
- Elementor snippet `5549` `SX / Tawk.to Live Chat Widget`: `publish`
- Snippet `5549` sekarang berisi direct Tawk chat button, bukan embedded loader.
- Live HTML contact page berisi `https://tawk.to/chat/66666723981b6c56477b687b/1i0005pb0`
- Live HTML tidak lagi berisi blocked loader `https://embed.tawk.to/66666723981b6c56477b687b/1i0005pb0`
- Live HTML tidak lagi punya Tawk preconnect/dns-prefetch ke `embed.tawk.to` atau `va.tawk.to`

## Kronologi P0

### 1. Audit Awal

Audit awal dibuat di:

- `report.md`

Temuan utama:

- Taxonomy sitemap kosong ikut masuk sitemap index.
- Beberapa metadata ZH corrupt/terlalu pendek.
- Tawk.to memicu CORS/runtime error.
- Ada JavaScript runtime error `Unexpected token '|'`.
- Redirect `www` masih multi-hop dan downgrade dari HTTPS ke HTTP.
- AIOSEO scoring sebagian halaman rendah karena keyphrase/description/readability.
- Beberapa console error berasal dari AdSense `no_div`.

### 2. Backup Sebelum P0

Backup sebelum perubahan P0 dibuat di:

- `backups/2026-05-31/p0-fix/pre-state.json`

Backup tersebut berisi state AIOSEO options, WP settings, plugin list, dan Elementor snippets yang relevan.

### 3. AIOSEO Sitemap Fix

Perubahan:

- `options.sitemap.general.taxonomies = { all:false, included:[] }`
- `options.sitemap.html.taxonomies = { all:false, included:[] }`

Validasi:

- `https://suriota.com/sitemap.xml`: `200`
- `page-sitemap.xml`: masih ada
- `post-sitemap.xml`: masih ada
- `category-sitemap.xml`: tidak lagi listed, endpoint `404`
- `post_tag-sitemap.xml`: tidak lagi listed, endpoint `404`

Status: selesai.

### 4. Tawk.to Broken Widget Disabled

Awalnya snippet `5549` memuat:

- `https://embed.tawk.to/66666723981b6c56477b687b/1i0005pb0`
- `crossorigin="*"`

Masalah:

- Browser sample menunjukkan CORS/runtime error.
- Pada variasi test, `crossorigin="*"` memicu CORS block.
- Tanpa `crossorigin`, browser masih mencatat `ERR_BLOCKED_BY_ORB`.

Tindakan P0 awal:

- Snippet `5549` diubah dari `publish` ke `draft`.

Status P0 awal: selesai, error Tawk hilang.

### 5. Tawk Preconnect Cleanup

Snippet `5550` sebelumnya memuat preconnect/dns-prefetch ke:

- `https://embed.tawk.to`
- `https://va.tawk.to`

Setelah Tawk disabled, referensi ini dihapus agar tidak ada koneksi pihak ketiga yang tidak dipakai.

Status: selesai.

### 6. Metadata ZH Fix

Halaman yang diperbaiki via AIOSEO REST:

- `/zh/guanyu-women/`
- `/zh/gongye-wulianwang-jicheng/`
- `/zh/ai-gongye-fenxi/`
- `/zh/shuzihua-zhuanxing-zixun/`
- `/zh/gongye-gongcheng-zidonghua/`
- `/zh/surge-saas-pingtai/`

Validasi:

- Title/description live sudah tidak corrupt.
- Canonical tetap mengarah ke URL halaman masing-masing.

Status: selesai.

### 7. JavaScript Runtime Fix

Error:

- `Unexpected token '|'`

Sumber:

- Snippet `5599` `SX / Language Switcher Patch - New Pillar Pages`
- Regex live rusak: `location.pathname.replace(/^/+|/+$/g, '')`

Perubahan:

- Regex diperbaiki menjadi escaped slash regex valid: `location.pathname.replace(/^\/+|\/+$/g, '')`

Validasi:

- Live HTML tidak lagi memuat regex rusak.
- Playwright validation setelah fix menunjukkan `pageErrors = 0`.

Status: selesai.

### 8. Redirect WWW

Kondisi redirect tetap:

- `http://suriota.com/` -> `https://suriota.com/` -> `200`
- `https://www.suriota.com/` -> `http://suriota.com/` -> `https://suriota.com/` -> `200`
- `http://www.suriota.com/` -> `https://www.suriota.com/` -> `http://suriota.com/` -> `https://suriota.com/` -> `200`

Status: belum selesai.

Alasan:

- Perlu akses DNS/origin/Cloudflare/vhost.
- Tidak bisa diselesaikan dengan WordPress REST yang tersedia.

## Validasi Pasca P0

Artifact:

- `backups/2026-05-31/p0-fix/apply-results.json`
- `backups/2026-05-31/p0-fix/post-validation.json`
- `tmp/suriota-browser-validate.json`
- `tmp/browser-audit/*.png`

Hasil:

- Sample pages `200`.
- H1 valid: `1` per sample page.
- Schema utama masih tersedia.
- `pageErrors = 0`.
- Tawk CORS/runtime error hilang setelah Tawk embed dinonaktifkan.
- Sisa issue browser adalah AdSense `no_div` pada beberapa halaman tanpa slot iklan.

## Tawk.to Restore Attempt

### Tujuan

User meminta Tawk.to tetap digunakan. Tahap pertama saya restore sebagai direct chat button agar chat tetap tersedia tanpa memunculkan error embed.

### Direct Chat Button

Snippet `5549` diaktifkan kembali sebagai floating direct chat button.

URL:

- `https://tawk.to/chat/66666723981b6c56477b687b/1i0005pb0`

Validasi:

- Button muncul di EN: `Live Chat`
- Button muncul di ID: `Chat Kami`
- Button muncul di ZH: `在线咨询`
- Tidak ada request blocked ke `embed.tawk.to`
- Tidak ada Tawk console/page error dari direct button

Status: aktif sekarang.

Catatan:

- Direct chat button membuka Tawk chat, tetapi tidak sama dengan embedded Tawk visitor monitoring.

### User Clarification

User kemudian mengklarifikasi bahwa yang dibutuhkan adalah embedded Tawk agar visitor bisa dimonitor saat visit.

### Embedded Loader Tests

Embed resmi diuji dengan beberapa variasi:

1. Loader standar dengan `crossorigin="*"`
2. Loader tanpa `crossorigin`
3. Loader dengan `crossorigin="anonymous"`
4. Loader dengan `crossorigin="use-credentials"`
5. Direct iframe ke `https://tawk.to/chat/...`
6. Inline loader Tawk dari CDN
7. Inline loader Tawk yang dipatch agar tidak menambahkan `crossorigin`
8. Inline semua JS chunk Tawk dari CDN

Hasil:

- Loader standar gagal dengan CORS.
- Loader tanpa `crossorigin` gagal dengan `ERR_BLOCKED_BY_ORB`.
- Iframe chat tetap memanggil loader yang sama di dalam frame dan menghasilkan CORS block.
- Inline loader berhasil membuat sebagian object Tawk, tetapi chunk internal tetap gagal.
- Inline semua chunk membuat `Tawk_API` methods muncul, tetapi request internal `va.tawk.to/v1/widget-settings`, `va.tawk.to/v1/session/start`, dan language JSON tetap CORS-blocked.

Kesimpulan teknis:

- Dari sisi browser saja, embedded Tawk penuh tidak bisa dibuat bersih pada kondisi CDN/API saat ini.
- Untuk visitor monitoring penuh, solusi perlu salah satu dari:
  - konfigurasi resmi Tawk/plugin yang menghasilkan loader compatible,
  - server-side proxy yang mengatur headers dan meneruskan endpoint Tawk,
  - Cloudflare Worker/rewrite khusus,
  - atau update/fix dari sisi Tawk CDN/API.

## Code Snippets Incident

### Tujuan

Saya mencoba jalur server-side proxy yang tidak mengedit theme langsung, dengan memasang plugin `Code Snippets` dari WordPress.org agar bisa membuat endpoint/proxy PHP khusus Tawk.

### Yang Terjadi

Setelah plugin `Code Snippets` diaktifkan, WordPress menjalankan snippet lama yang ternyata sudah ada di database plugin tersebut. Snippet lama itu memanggil:

- `clear_cache()` pada object null

Error:

- `Uncaught Error: Call to a member function clear_cache() on null`
- File error: `wp-content/plugins/code-snippets/php/snippet-ops.php(663) : eval()'d code`

Dampak sementara:

- `/`
- `/wp-json`
- `/wp-login.php`
- WP REST plugin deactivate

sempat return `500`.

### Recovery

Pada saat terakhir dicek, site sudah kembali normal:

- `/`: `200`
- `/contact/`: `200`
- `/wp-json`: `200`

Plugin status terakhir:

- `code-snippets-test/code-snippets`: inactive

Artinya folder/plugin kemungkinan sudah dinonaktifkan/direname di layer server, atau WordPress berhasil membaca plugin tersebut sebagai inactive.

Backup terkait:

- `backups/2026-05-31/tawk-restore/plugins-before-code-snippets.json`
- `backups/2026-05-31/tawk-restore/before-5549.json`
- `backups/2026-05-31/tawk-restore/after-5549.json`
- `backups/2026-05-31/tawk-restore/after-5549-v2.json`

## Current Risk Register

| Risk | Status | Impact | Recommendation |
|---|---:|---|---|
| Tawk embedded visitor monitoring belum pulih | Open | Visitor monitoring Tawk belum bekerja sebagai embed | Gunakan Tawk plugin/dashboard official config atau buat proxy via Cloudflare/origin dengan rollback plan. |
| Direct Tawk button aktif | Active | Chat masih bisa diakses, tapi bukan passive visitor monitor | Keep sementara agar user tetap bisa chat. |
| Code Snippets inactive setelah incident | Watch | Jangan aktifkan tanpa audit snippet DB | Hapus plugin atau audit tabel snippet sebelum re-activate. |
| WWW redirect multi-hop | Open | SEO canonical/redirect hygiene kurang ideal | Fix di Cloudflare/origin. |
| AdSense `no_div` | Open | Console error di beberapa halaman | Load AdSense hanya saat ada slot iklan, setelah keputusan monetisasi. |

## Rekomendasi Lanjutan

1. Jangan aktifkan `Code Snippets` lagi sebelum isi database snippet-nya diaudit atau dibersihkan.
2. Pertahankan direct Tawk button sementara karena sudah aktif dan tidak memicu error embed.
3. Untuk visitor monitoring Tawk, pilih salah satu jalur:
   - Update/configure plugin Tawk official melalui WP Admin setelah login, lalu test real browser.
   - Pakai Cloudflare Worker untuk proxy Tawk assets/API dengan header yang benar.
   - Buat custom mini-plugin PHP khusus proxy Tawk, bukan via `Code Snippets`.
4. Fix redirect `www` di DNS/origin/Cloudflare.
5. Pertimbangkan guard AdSense agar script tidak memanggil ad slot pada halaman tanpa `ins.adsbygoogle`.

## File Report Terkait

- Audit awal: `report.md`
- Report P0 sebelumnya: `report-p0-fix-2026-05-31.md`
- Report kronologis ini: `report-p0-to-tawk-status-2026-05-31.md`

