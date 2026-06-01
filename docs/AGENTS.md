# AGENTS.md — Website Suriota

## 🎯 Tujuan
Improvement UI/UX untuk website https://suriota.com menggunakan Elementor via MCP.

## 🔌 MCP Connection
- **Server:** `elementor-mcp`
- **Site:** https://suriota.com
- **Plugin:** MCP Tools for Elementor v1.7.4 (113 tools) via MCP Adapter v0.5.0
- **Auth:** Application Password (disimpan di wrapper)

## 🛠️ Semua Tools yang Bisa Dipakai

### Elementor MCP (Primary)
- `elementor-mcp-list-pages` — Lihat semua page Elementor
- `elementor-mcp-get-page-structure` — Lihat struktur elemen suatu page
- `elementor-mcp-get-element-settings` — Lihat setting spesifik elemen
- `elementor-mcp-find-element` — Cari elemen by type/widget
- `elementor-mcp-get-global-settings` — Lihat global kit colors/typography
- `elementor-mcp-add-container`, `update-container`, `update-element`, `batch-update`
- `elementor-mcp-add-heading`, `add-text-editor`, `add-image`, `add-button`, `add-icon-box`
- `elementor-mcp-export-page` — Backup sebelum edit

### Puppeteer (Visual Audit)
- Screenshot before/after
- Visual regression testing
- Mobile responsive check

### Fetch (Research)
- Crawl competitor websites
- Research UI/UX trends
- Analyze similar engineering consulting sites

### SQLite (Tracking)
- `website_pages` table — 20 pages
- `website_audit` table — findings & tasks
- Query progress dan status

### Sequential Thinking (Planning)
- Deep analysis kompleks
- Prioritization matrix
- Roadmap generation

## 📝 Workflow Wajib

1. **Sebelum Edit:**
   - Panggil `elementor-mcp-export-page` untuk backup
   - Atau panggil `elementor-mcp-get-page-structure` untuk audit
   - Screenshot current state via puppeteer

2. **Saat Edit:**
   - Identifikasi element_id yang mau diubah
   - Gunakan `elementor-mcp-update-element` untuk partial update
   - Atau `elementor-mcp-batch-update` untuk multiple changes

3. **Setelah Edit:**
   - Screenshot hasil via puppeteer (kalau langsung terlihat)
   - Inform user untuk clear cache/regenerate CSS di WP Admin
   - Update `website_audit` status di sqlite
   - Sarankan preview page

## 🤖 Agent Swarm Usage

Gunakan `swarm-config.md` sebagai referensi decomposition.

### Pattern yang Direkomendasikan
```
1. Launch parallel explore agents untuk audit
2. Aggregate hasil ke dalam sqlite + markdown report
3. Launch coder agents untuk implementasi per page/cluster
4. Verify dengan puppeteer screenshots
```

## 🎨 Design Guidelines Suriota

### Brand Identity
- **Nama:** PT Surya Inovasi Prioritas (SURIOTA)
- **Fokus:** Industrial IoT, Automation, Electrical, Renewable Energy
- **Warna utama:** Cek `backups/elementor_colors.json`
- **Typography:** Cek `backups/elementor_typography.json`

### Temuan Audit Awal (Homepage)
1. Hero illustration (rocket/astronaut) terlalu playful untuk engineering consulting
2. Product cards flat — butuh hover effects dan CTA buttons
3. Client logos section tanpa heading "Trusted By"
4. Portfolio table terlalu plain — consider card layout
5. Contact form tanpa visible validation states
6. Typography hierarchy bisa lebih kuat

### ✅ Completed Improvements

#### About Us (page-29) — Major Refactor 2026-05-16 — Industrial Editorial v1
**Design System "sx-" locked** — see `design-system/DESIGN-SYSTEM.md` + `design-system/sx-design-system.css`.

- **Aesthetic**: Industrial Editorial (Linear/Siemens/Bosch inspired). Disciplined B2B refinement.
- **Typography upgrade**: Added Plus Jakarta Sans (display) + IBM Plex Mono (numerics/eyebrows) alongside Poppins (body)
- **Color tokens**: Added `--sx-amber #C8851F` industrial accent + `--sx-teal-deep #0E3942` high-contrast headings
- **Numbered indicators**: Every multi-item section uses `01-04` mono badges (Visi/Misi, Bidang Fokus, Trust cards)
- **All emoji replaced with line-art SVG icons** (Heroicons-style 1.5px stroke)
- **Stats**: Mono tabular numerics with hairline separators; line-art icons; reveal stagger
- **Section refactor**: Hero, Stats, Visi/Misi, Siapa SURIOTA, Bidang Fokus, Mengapa SURIOTA — all v2
- **CTA dual-action**: Primary Drive + WA `wa.me/6285835672476` (#075E54 WCAG AAA) + Form `/contact/`
- **Saved Elementor Templates** for cross-page reuse:
  - Template `4675` — SX / Stats Bar
  - Template `4677` — SX / Service Card Grid 01-04
  - Template `4679` — SX / Trust Cards (Mengapa Memilih)
  - Template `4681` — SX / CTA Dual-Action (Primary + WA + Form)
- **SEO**: Extended JSON-LD `@graph` — Organization + LocalBusiness + AboutPage + BreadcrumbList + 4× Service entries
- **A11y**: WCAG 2.1 AA pass (contrast, focus-visible, reduced-motion, touch targets ≥44px, pulse ≤3 iter)
- **Responsive**: 4 breakpoints (xs/sm/tb/lg) + touch-device tap-flash + per-section padding_tablet/padding_mobile
- **Custom CSS**: Full `sx-` design system layer added to page custom CSS (~360 lines)

**Reuse playbook**: Copy `design-system/sx-design-system.css` to next page's Custom CSS, insert SX templates as starting sections, apply `.sx-eyebrow` + `.sx-card-num` patterns.

#### Homepage (page-12) — Reverted 2026-05-14
Visual enhancement V4 di-revert karena feedback "jadi hancur".

**Yang di-revert**:
- Custom CSS dihapus dari 10 halaman (homepage + service + product)
- 3 Counter widgets dihapus dari hero
- Section padding dikembalikan ke default
- Shape dividers dihapus
- Heading sizes dikembalikan ke default
- Portfolio CTA padding dikembalikan

**Yang dipertahankan** (tidak merusak):
- About Us (page-29) refactoring — tidak diubah
- Internship (page-1127) refactoring — tidak diubah

#### About Us (page-29) — Refactored 2026-05-13
- **Stats section**: Updated "10+ Tahun" → "2+ Tahun Beroperasi", applied `clamp()` responsive sizing
- **Heading fix**: Elementor heading changed H1→H2 (duplicate H1 fix), entry-title hidden via CSS
- **4 Bidang Fokus SURIOTA**: Rebuilt with inline CSS card layout (white cards, emoji icons, hover effects)
- **Makna Logo SURIOTA**: Rebuilt with inline CSS card layout (4 meaning cards with icons)
- **Custom CSS added**: `.entry-title` hide, card hover transitions, CTA button pulse
- **Mobile verified**: Cards stack vertically on 375px, stats use 2-column grid, readable typography

#### Internship (page-1127) — Refactored 2026-05-13
- **Compact fit-to-screen layout**: Addressed user feedback "too much empty space, too much scrolling"
- **Hero section**: Side-by-side text + poster on desktop (flex wrap), stacked on mobile
  - H1 "Internship Program" + subtitle + CTA button left, **poster image right (jelas terpampang)**
  - Poster size: `clamp(320px, 35vw, 440px)` — **tidak dihapus**, jelas terlihat
- **Quick stats**: Inline pills — ⏱ 3–6 Bulan | 🌎 Hybrid | 🎯 4 Posisi
- **Position cards**: 4 cards in 1 row on desktop (`min-width:110px`, `flex:1`), 2×2 grid on mobile
  - R&D App Developer, DevOps Engineer, QA Specialist, UI/UX Designer
- **Why Join merged**: Combined into intro paragraph to eliminate full section
- **Tech stack tags**: Compact inline badge row (Next.js, React, Prisma, MySQL, PostgreSQL, Git, Caprover, Ubuntu VPS, Figma)
- **Progressive Disclosure (Collapsible Sections)**: Based on UX research — Kualifikasi & Dokumen + Benefit use native HTML `<details>` elements
  - Default: collapsed — saves ~250px vertical space
  - Click "Klik untuk lihat" badge to expand
  - Works on desktop & mobile without JavaScript
- **CTA section**: Compact 3-step inline cards + "Daftar Sekarang via Email" button
- **Entry title hidden**: `.entry-title {display:none !important;}`
- **Typography scale (Retina-friendly)**: 
  - H1: `clamp(32px, 5vw, 48px)`
  - H2: `24px`
  - Body: `clamp(15px, 2vw, 17px)`
  - Card title: `16px`
  - Card desc: `14px`
  - Badges/pills: `13px`
  - List items: `15px`
- **Verified**: Desktop (1920px) ~1956px height, poster jelas terlihat, mobile (375px) collapsible works correctly, retina-readable

### Best Practices
- Pertahankan konsistensi dengan global design tokens
- Gunakan spacing yang cukup antar section
- Pastikan CTA button jelas dan kontras
- Optimasi mobile responsive (cek breakpoints)
- Gambar produk/services harus high quality

## ⚠️ Aturan Safety
- Jangan hapus page content tanpa export backup
- Selalu duplikat elemen sebelum modify (kalau ragu)
- Batch update untuk efisiensi, tapi jangan terlalu banyak sekaligus
- Inform user setiap kali melakukan perubahan signifikan
- Regenerate CSS setelah setiap session edit

## 📂 Lokasi Backup & Scripts
- Backup otomatis: `node scripts/backup-all.js`
- Screenshot audit: `node scripts/screenshot-audit.js`
- Semua backup di `backups/`
- Semua screenshot di `screenshots/`

## 📊 Page Reference (Suriota)

| Page | post_id |
|------|---------|
| Homepage | 12 |
| About Us | 29 |
| Desain Grafis | 33 |
| Automation | 35 |
| Electrical | 37 |
| Renewable Energy | 39 |
| Teknologi Informasi | 41 |
| Tentang | 376 |
| Portfolio | 839 |
| Modbus Gateway | 934 |
| Waste Water Loger | 929 |
| Water Treatment | 945 |
| Internship | 1127 |
| SURGE-Energy Mapping | 1542 |
| SURGE-Vessel Tracking | 1546 |
| SURGE-Water Analytic | 1547 |
| ISO-M485 SERIES | 1740 |
| THM-30MD | 1741 |
| PM1611-WD | 1742 |
| RS-485 Surge Protector | 1765 |
