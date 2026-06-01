# SURIOTA Website SEO, Indexing, AIOSEO, Plugin Audit

Tanggal audit: 2026-05-31  
Website: https://suriota.com  
Mode audit: read-only terhadap website live, REST API WordPress, sitemap, robots, browser render, dan arsip lokal repo.

## Ringkasan Eksekutif

Kondisi dasar website **cukup sehat untuk crawling dan indexing halaman utama**: seluruh URL yang dicrawl merespons `200`, robots.txt tidak memblokir halaman publik, AIOSEO aktif, sitemap live, canonical tersedia, structured data aktif, dan halaman inti EN/ID/ZH sudah punya metadata.

Namun website **masih perlu optimasi targeted**, terutama pada:

1. **Sitemap dan taxonomy archive**: sitemap memasukkan 114 URL category/tag/language archive. Semua taxonomy archive yang dicrawl punya skor teknis rendah, tidak punya meta description, dan berpotensi menjadi thin/low-value indexed pages.
2. **Legacy service URLs**: 28 legacy service pages sudah `noindex` di AIOSEO dan dikeluarkan dari sitemap, tetapi masih publish dan beberapa masih menghasilkan canonical/metadata duplikat ke pillar pages. Ini bukan rusak, tetapi perlu keputusan: tetap `noindex` sementara atau 301 penuh ke pillar.
3. **Meta description EN/ID/ZH pillar dan ZH pages**: beberapa halaman penting masih terlalu pendek atau terlalu panjang. ZH pillar/core rata-rata masih lemah untuk snippet karena deskripsi 52-98 karakter.
4. **AIOSEO scoring internal**: REST AIOSEO mengembalikan skor nonzero hanya untuk 3 dari 161 page/post (`Homepage 85`, `Internship 68`, `Waste Water Logger 80`). Banyak halaman punya metadata live yang benar, tetapi skor AIOSEO tetap `0`, kemungkinan karena TruSEO/Page Analysis tidak membaca konten Elementor/static rendered dengan benar atau belum diproses ulang.
5. **Runtime JS/plugin issue**: browser render menemukan error sitewide dari Tawk.to (`CORS/Failed to load`) dan satu page error `Unexpected token '|'`. Ini tidak menghentikan SEO tags/schema, tetapi mengganggu hygiene teknis dan bisa berdampak pada UX/performance.
6. **Redirect canonicalization www**: `https://www.suriota.com/` redirect lewat `http://suriota.com/` sebelum final HTTPS. Ini harus dipangkas menjadi 1 hop langsung ke `https://suriota.com/`.

Kesimpulan: **perlu optimize**, tetapi bukan rebuild besar. Fokusnya technical SEO cleanup, sitemap pruning, AIOSEO reprocess/score hygiene, ZH metadata, dan JS/plugin cleanup.

## Tools dan Metode

Skill/plugin yang dipakai:

- Browser skill dibaca dan dicoba sesuai workflow; backend in-app `iab` tidak tersedia pada sesi ini.
- Playwright skill digunakan sebagai fallback browser render.
- Multi-agent digunakan untuk dua sidecar audit: arsip lokal/repo dan website publik.
- Web reference/fetch digunakan untuk baseline terbaru Google Search Central dan AIOSEO.
- WordPress REST API digunakan read-only; kredensial dari `.env` tidak disalin ke laporan.
- Script audit dibuat di `tmp/suriota-seo-audit.mjs` dan `tmp/suriota-browser-validate.mjs`.

Artefak hasil:

- `tmp/suriota-seo-audit.json` - full crawl 277 URL.
- `tmp/suriota-browser-validate.json` - browser render 7 halaman kunci.
- `tmp/suriota-aioseo-scores.json` - AIOSEO REST page/post score snapshot.
- `tmp/browser-audit/*.png` - screenshot halaman sampel.

## Referensi Baseline

Referensi yang dipakai:

- Google Search Central SEO Starter Guide: title, structure, canonicalization, linking, dan praktik SEO dasar.
- Google Search Central Robots Meta/X-Robots-Tag: `noindex`, `nofollow`, `nosnippet`, dan preview controls.
- Google Search Central Canonical URLs: canonical dipakai untuk konsolidasi duplikat; sitemap URL dipakai sebagai sinyal canonical.
- Google Search Central Localized Versions: `hreflang` untuk variasi bahasa/region dan `x-default`.
- Google Search Central AI Features: praktik SEO biasa tetap relevan untuk AI Overviews/AI Mode; snippet controls seperti `nosnippet`, `max-snippet`, `noindex` juga memengaruhi AI features.
- AIOSEO TruSEO/Page Analysis docs: skor adalah rekomendasi, berbasis Page Analysis plus Focus Keyword/Additional Keywords; tidak wajib 100, tetapi harus dipakai untuk menjaga praktik on-page SEO.

## Coverage

Live crawl:

| Area | Jumlah | Status |
|---|---:|---|
| Sitemap URLs | 249 | Terbaca dari AIOSEO sitemap index |
| REST pages | 97 | Published pages |
| REST posts | 64 | Published posts |
| Total crawled unique URLs | 277 | Semua `200` |
| Sitemap files | 6 | Semua `200` |
| Browser-render sample | 7 | Semua `200` |

Sitemap files:

- `/sitemap.xml`
- `/post-sitemap.xml`
- `/page-sitemap.xml`
- `/category-sitemap.xml`
- `/post_tag-sitemap.xml`
- `/language-sitemap.xml`

## Indexing dan Crawlability

Positif:

- `robots.txt` live dan valid.
- Public pages tidak diblokir robots.txt.
- Sitemap AIOSEO live dan disebut di robots.txt.
- Semua 277 URL yang dicrawl merespons `200`.
- Canonical tag ada di semua URL yang dicrawl.
- Tidak ada schema JSON-LD parse error.

Risiko:

- Sitemap memasukkan 9 category URLs dan 105 tag URLs. Semua taxonomy URLs punya meta description kosong.
- Public sub-agent menemukan `lastmod` taxonomy/language sitemap mencurigakan pada `1970-01-01T00:00:00+00:00` di sampel.
- `www` redirect masih multi-hop dan sempat downgrade ke HTTP:
  - `https://www.suriota.com/` -> `http://suriota.com/` -> `https://suriota.com/`
  - `http://www.suriota.com/` -> `https://www.suriota.com/` -> `http://suriota.com/` -> `https://suriota.com/`

Rekomendasi:

1. Di AIOSEO Sitemap settings, exclude taxonomy yang tidak punya strategi SEO: `post_tag`, dan category yang tipis/duplikat.
2. Jika category tertentu mau diindex, isi term description, SEO title, meta description, dan jadikan landing archive yang berguna.
3. Ubah Cloudflare/origin redirect agar semua `www` dan HTTP langsung 301 ke `https://suriota.com/$path` satu hop.

## Metadata dan AIOSEO

Ringkasan teknis crawler:

| Group | Count | Avg Score | Below 80 | Missing Desc | Bad Desc Length | Bad Title Length |
|---|---:|---:|---:|---:|---:|---:|
| All crawled | 277 | 81 | 150 | 114 | 54 | 155 |
| Taxonomy archive | 114 | 69 | 114 | 114 | 0 | 114 |
| REST pages | 97 | 84 | 34 | 0 | 51 | 40 |
| REST posts | 64 | 100 | 0 | 0 | 1 | 0 |
| Main/lang core sample | 75 | 82 | 34 | 0 | 47 | 36 |

Catatan penting: raw HTML crawler sempat membaca beberapa halaman dengan 2 H1, tetapi browser-render Playwright menunjukkan halaman sampel sudah menjadi 1 H1 setelah runtime. Jadi H1 raw warning dianggap **needs monitoring**, bukan blocker.

Halaman penting yang perlu metadata polish:

| URL | Masalah |
|---|---|
| `/contact/` | Title terlalu pendek: `Contact - SURIOTA`; description 162 chars sedikit panjang |
| `/industrial-engineering-automation/` | Title 62 chars dan description 403 chars |
| `/surge-saas-platform/` | Description 402 chars |
| `/ai-industrial-analytics/` | Description 365 chars |
| `/zh/gongye-wulianwang-jicheng/` | Title 26 chars, description 71 chars, content sekitar 280 words |
| `/zh/shuzihua-zhuanxing-zixun/` | Description 52 chars |
| `/zh/gongye-gongcheng-zidonghua/` | Description 69 chars |
| `/zh/surge-saas-pingtai/` | Live/API description sangat pendek |
| `/zh/guanyu-women/` | Title live terlihat corrupt: `?? SURIOTA - ?????????` |

AIOSEO score internal:

- AIOSEO active: `4.9.7.2`.
- AIOSEO advanced `truSeo` aktif.
- Focus keyphrase kosong pada 96/161 page/post.
- REST AIOSEO score snapshot:
  - Homepage: 85
  - Internship: 68
  - Waste Water Logger: 80
  - 158 lainnya: 0
- 51 item masih memiliki AIOSEO title placeholder `#post_title #separator_sa #site_title`.

Interpretasi: live SEO tags sudah keluar di HTML untuk banyak halaman, tetapi AIOSEO score dashboard kemungkinan belum sinkron/terproses untuk Elementor pages. Ini perlu validasi admin-side, bukan hanya REST.

Rekomendasi:

1. Reprocess/update AIOSEO analysis untuk Elementor pages setelah metadata final.
2. Set focus keyphrase untuk halaman money pages dan 15 pillar pages.
3. Perbaiki ZH title/meta yang corrupt/terlalu pendek.
4. Batasi meta description ke sekitar 120-160 karakter untuk halaman prioritas.
5. Jangan mengejar skor 100 secara buta; pakai AIOSEO score sebagai guardrail, bukan pengganti kualitas konten.

## Canonical, Duplikasi, dan Legacy URLs

Positif:

- Tidak ada canonical mismatch terhadap final URL pada crawler.
- Legacy pages yang dikeluarkan dari sitemap terdeteksi `noindex` melalui AIOSEO snapshot.

Risiko:

- Banyak legacy service URLs masih publish dan canonical/meta-nya menunjuk atau duplikat dengan pillar baru. Ini benar jika strategi sementara adalah consolidation, tetapi tidak ideal jika targetnya crawl budget bersih.
- 28 URLs noindex dari AIOSEO:
  - EN legacy: `/software-as-a-service/`, `/data-analytics/`, `/artificial-intelligence/`, `/digital-consulting/`, `/internet-of-things/`, `/water-treatment/`, `/renewable-energy/`, `/electrical/`, `/automation/`
  - ID legacy: `/id/artificial-intelligence-id/`, `/id/digital-consulting-id/`, `/id/data-analytics-id/`, `/id/internet-of-things-id/`, `/id/renewable-energy-id/`, `/id/automation-id/`, `/id/electrical-id/`, `/id/saas-id/`, `/id/water-treatment-id/`
  - ZH legacy: `/zh/saas/`, `/zh/shujufenxi/`, `/zh/rengong-zhineng/`, `/zh/shuzihua-zixun/`, `/zh/iot/`, `/zh/shuichuli/`, `/zh/kezaisheng-nengyuan/`, `/zh/dianqi-gongcheng/`, `/zh/zidonghua/`
  - Utility: `/unsubscribe/`

Rekomendasi:

1. Untuk legacy service pages: jika tidak dibutuhkan user, ubah ke 301 redirect ke pillar baru.
2. Jika masih dibutuhkan untuk UX/internal campaign, pertahankan `noindex` dan pastikan tidak masuk sitemap.
3. Pastikan internal navigation hanya mengarah ke pillar baru, bukan legacy.

## Hreflang dan Multilingual

Positif:

- EN/ID/ZH hreflang hadir di halaman utama dan pillar pages.
- Browser sample menunjukkan nav per bahasa sudah berubah sesuai locale.
- Polylang active dan Connect Polylang for Elementor active.

Risiko:

- Sub-agent public menemukan duplikasi hreflang pada service pages: EN/ID/ZH muncul dua kali sebelum `x-default`.
- Beberapa legacy/noindex language pages masih publish.
- Locale ZH masih perlu dipastikan: `zh` vs `zh-CN` tergantung target market. Google menerima language code, tetapi jika target Mandarin Simplified/China spesifik, `zh-CN` lebih eksplisit.

Rekomendasi:

1. Audit source hreflang: hindari output ganda dari AIOSEO + Polylang + snippet.
2. Untuk halaman pillar, targetkan satu set hreflang bersih: `en`, `id`, `zh` atau `zh-CN`, dan `x-default`.
3. Jangan masukkan noindex legacy pages ke hreflang cluster jika ingin cluster bersih.

## Structured Data

Positif:

- JSON-LD hadir di semua URL crawled.
- Tidak ada parse error.
- Schema graph utama aktif:
  - `Organization`
  - `LocalBusiness`
  - `WebSite`
  - `WebPage`
  - `BreadcrumbList`
  - `OfferCatalog`
- Page-specific schema terdeteksi:
  - Pillars: `Service`, `FAQPage`
  - SURGE SaaS: `SoftwareApplication`, `FAQPage`
  - Contact: `ContactPage`, `FAQPage`
  - Portfolio: `ItemList`
  - Posts: `BlogPosting`

Risiko:

- FAQ schema masih ada; perlu dipantau karena Google SERP support untuk beberapa rich result type berubah dari waktu ke waktu. Schema tetap bisa berguna untuk machine understanding, tetapi jangan bergantung pada rich result.
- Contact page sebelumnya pernah punya risiko duplicate LocalBusiness; live sample sekarang menunjukkan schema luas tapi perlu validasi Rich Results/Schema Validator untuk graph detail.

Rekomendasi:

1. Pertahankan `@id` konsisten untuk `https://suriota.com/#organization`.
2. Jalankan validator schema eksternal setelah setiap perubahan snippet besar.
3. Untuk portfolio/project posts, lanjutkan enrichment `CreativeWork`/`Project` hanya jika data faktual tersedia.

## AI SEO / AI Search Readiness

Berdasarkan Google Search Central AI Features, tidak ada teknik “AISEO” terpisah yang menggantikan SEO teknis. Faktor yang relevan untuk AI Overviews/AI Mode tetap:

- Crawlable dan indexable content.
- Canonical bersih.
- Snippet controls tidak membatasi konten penting.
- Konten jelas, faktual, dan mudah diekstrak.
- Structured data akurat.
- Halaman menjawab intent secara langsung.

Kondisi SURIOTA:

- Halaman pillar EN/ID/ZH sudah punya structured data dan konten topikal.
- `noindex` hanya muncul pada utility/legacy, bukan halaman utama.
- Risiko AISEO terbesar saat ini adalah thin/duplikat taxonomy archive, ZH descriptions yang terlalu pendek, dan legacy canonical/noindex cluster yang membingungkan jika tidak dipangkas.

Rekomendasi AISEO:

1. Tambahkan bagian Q&A/factual snippets pada pillar pages, tetapi hindari FAQ spam.
2. Perjelas entity facts: legal company name, Batam/Indonesia coverage, product names, protocols, compliance terms seperti KLHK/SPARING.
3. Tambahkan author/reviewer atau company expertise signals pada artikel teknis.
4. Jangan gunakan `nosnippet` pada halaman yang ingin tampil di AI features.

## Plugin dan Fungsi

Plugin aktif via REST:

| Plugin | Versi | Status Audit |
|---|---:|---|
| All in One SEO | 4.9.7.2 | Aktif, sitemap/meta/schema berjalan; scoring internal perlu sync |
| Elementor | 4.1.1 | Aktif |
| Elementor Pro | 4.1.0 | Aktif |
| Polylang | 3.8.4 | Aktif |
| Connect Polylang for Elementor | 2.5.5 | Aktif |
| Redirection | 5.7.5 | Aktif |
| WP-Optimize | 4.5.4 | Aktif; cache header Cloudflare masih dynamic pada sample |
| EWWW Image Optimizer | 8.7.0 | Aktif |
| WP Mail SMTP | 4.8.0 | Aktif |
| WP Table Builder | 2.1.14 | Aktif |
| Tawk.to Live Chat | 0.9.3 | Aktif tetapi script gagal load di browser sample |
| MCP Adapter | 0.5.0 | Aktif |
| MCP Tools for Elementor | 1.7.4 | Aktif |
| SURIOTA Click Tracker | 1.7.1 | Aktif dan route publik/auth berfungsi |
| Prime Mover | 2.1.5 | Aktif |

SURIOTA Click Tracker validation:

- `/wp-json/suriota/v1` route index: `200`.
- `/wp-json/suriota/v1/go`: `302` ke `/portfolio/` default; whitelist destination ada di plugin.
- `/wp-json/suriota/v1/clicks`: `401` tanpa auth, benar.
- `/wp-json/suriota/v1/unsubs`: `401` tanpa auth, benar.
- `/wp-json/suriota/v1/unsub`: GET render confirmation, POST baru record; ini baik untuk menghindari false unsubscribe dari scanner.
- `/ads.txt`: `200` dan berisi publisher line.
- `/webhook`: `400` tanpa challenge/secret, expected.
- `/webhook/meta`: `403` tanpa verify token, expected.
- `/instagram-oauth-callback`: `200`, page handler aktif.

Masalah plugin/runtime:

- Tawk.to script gagal CORS di semua browser sample:
  - `Access to script at https://embed.tawk.to/... has been blocked by CORS policy`
  - `Failed to load resource: net::ERR_FAILED`
- Page error sitewide:
  - `Unexpected token '|'`
- GA4 collect request abort muncul di Playwright headless; ini sering normal di test environment, tetapi tetap perlu cek di browser biasa/Tag Assistant.

Rekomendasi:

1. Disable atau fix Tawk.to property jika belum dipakai. Catatan lokal sudah menyebut snippet blocker 5528; live masih mencoba load script.
2. Cari sumber JS `Unexpected token '|'` dari snippet/minified footer; kemungkinan snippet custom atau optimizer.
3. Validasi GA4 dengan Tag Assistant atau Realtime setelah JS cleanup.

## Prioritas Optimasi

### P0 - High Impact / Low Risk

1. Exclude `post_tag` sitemap dan noindex tag archives yang tidak punya strategi SEO.
2. Fix redirect `www` langsung ke canonical HTTPS satu hop.
3. Fix Tawk.to script gagal load atau disable sepenuhnya.
4. Perbaiki corrupted title ZH `/zh/guanyu-women/`.

### P1 - SEO Core

1. Finalisasi 15 pillar pages: meta description 120-160 chars, focus keyphrase, AIOSEO reprocess.
2. Putuskan legacy service URLs: 301 ke pillar atau tetap noindex tanpa internal links.
3. Hreflang dedup agar hanya satu set alternate per cluster.
4. Perbaiki ZH metadata pendek pada pillar/core pages.

### P2 - Content dan AI Readiness

1. Tambah factual Q&A/summary sections untuk pillar pages.
2. Perkuat artikel teknis dengan author/company expertise, dates, dan internal links ke product/service.
3. Buat strategy untuk category archive yang akan tetap indexable.

### P3 - Monitoring

1. Submit sitemap ulang di Google Search Console setelah taxonomy pruning.
2. Inspect live URL untuk 5 pillar EN/ID/ZH dan legacy noindex sample.
3. Pantau coverage: indexed, crawled-currently-not-indexed, duplicate-with-canonical, excluded-by-noindex.

## Validasi Akhir

Yang sudah tervalidasi:

- 277 URL live dicrawl.
- 6 sitemap files dicek.
- 7 halaman sampel dirender dengan browser.
- WordPress plugin list dibaca via REST authenticated read-only.
- AIOSEO options, sitemap, robots, schema, canonical, hreflang, dan meta tags dicek.
- Custom plugin SURIOTA Click Tracker diuji endpoint publik dan auth-protected behavior-nya.

Yang tidak bisa divalidasi penuh dari sesi ini:

- Google Search Console coverage aktual, karena tidak ada konektor GSC.
- Rich Results Test live resmi, karena tidak ada API lokal yang digunakan.
- Browser in-app Codex, karena backend `iab` tidak tersedia; Playwright terminal dipakai sebagai fallback.

