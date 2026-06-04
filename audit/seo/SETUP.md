# suriota Google SEO toolkit — setup (one-time)

The toolkit is **already built**. It only needs credentials wired.

> Everything here is a **you-side** step (needs your authenticated Google login).
> Claude cannot create credentials, enable APIs, or grant property access.

## Pick an auth mode

- **OAuth (RECOMMENDED — see Part O below).** Uses your own Google account
  (`chanalva@suriota.com`, already a GSC Owner). Search Console refuses to add
  service-account emails as users on this property, so OAuth is the path of least
  resistance and gives Indexing API access for free (you're an Owner).
- **Service account (Part A).** Only if you can get the SA email added to the
  property. Kept here for reference.

GCP project in use: **named-sequencer-458710-n1** (where the `suriota-seo-bot` SA
+ OAuth client live). The 3 API-enable links below already point to it.

---

## Part O — OAuth user credentials (recommended)

1. **OAuth consent screen** — GCP → APIs & Services → **OAuth consent screen**
   (project named-sequencer-458710-n1).
   - If suriota.com is **Google Workspace**: User Type = **Internal** → no
     verification needed, refresh tokens don't expire. (best)
   - If not Workspace: **External** → fill app name + your email → under
     **Test users** add `chanalva@suriota.com`. (refresh token then lasts until
     re-consent; just re-run auth_oauth.py if it expires)

2. **Create the OAuth client** — APIs & Services → **Credentials** →
   *Create credentials* → **OAuth client ID** → Application type = **Desktop app**
   → name it → Create → **Download JSON** → save as `audit/seo/client_secret.json`
   (git-ignored).

3. **Enable the 3 APIs** (same as step 3 below).

4. **Run the flow:**
   ```
   python audit/seo/auth_oauth.py
   ```
   A browser opens → sign in as `chanalva@suriota.com` → Allow. Token saved to
   `audit/seo/oauth_token.json`. Then `python audit/seo/check.py`.

   *(Indexing API works automatically because you're a GSC Owner. GA4 still needs
   `GA4_PROPERTY_ID` in `.env` and your account to have GA4 access — you do.)*

---

## Part A — Service account (alternative, covers GSC + Indexing + GA4)

> Three of the four capabilities share **one service account**; Custom Search uses
> an API key + a Programmable Search Engine.

1. **Create the service account**
   - GCP Console → IAM & Admin → **Service Accounts** → *Create service account*
     (https://console.cloud.google.com/iam-admin/serviceaccounts?project=named-sequencer-458710-n1)
   - Name: `suriota-seo-bot` → Create → skip optional roles → Done.

2. **Download its JSON key**
   - Click the new SA → **Keys** tab → *Add key* → *Create new key* → **JSON** → Create.
   - Save the downloaded file as: `audit/seo/sa.json`
     (already git-ignored; never commit it). The SA email looks like
     `suriota-seo-bot@named-sequencer-458710-n1.iam.gserviceaccount.com` — note it.

3. **Enable the three APIs** (click each, press *Enable*):
   - Search Console API → https://console.cloud.google.com/apis/library/searchconsole.googleapis.com?project=named-sequencer-458710-n1
   - Web Search Indexing API → https://console.cloud.google.com/apis/library/indexing.googleapis.com?project=named-sequencer-458710-n1
   - Google Analytics Data API → https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com?project=named-sequencer-458710-n1

4. **Grant the SA access to Search Console**
   - https://search.google.com/search-console → select the **suriota.com** property
   - Settings → **Users and permissions** → *Add user*
   - paste the SA email, permission = **Owner** *(Owner is required for the Indexing API; Full would work for read-only GSC but not indexing)*.

5. **Grant the SA access to GA4**
   - GA4 Admin → **Property access management** → add the SA email as **Viewer**.
   - GA4 Admin → **Property Settings** → copy the **numeric Property ID** (e.g. `498xxxxxx`).
     Put it in `.env`:  `GA4_PROPERTY_ID=498xxxxxx`
     (this is NOT the measurement id `G-X69D43F8QD`).

6. **(If your GSC property is URL-prefix, not domain)** set in `.env`:
   `GSC_SITE=https://suriota.com/`  — default assumes a domain property (`sc-domain:suriota.com`).

---

## Part B — Custom Search (rank tracking)

7. **Create a Programmable Search Engine**
   - https://programmablesearch.google.com/ → *Add* → name it, then in settings set
     **"Search the entire web"** ON (required — otherwise it only searches suriota.com).
   - Copy the **Search engine ID** (`cx`). Put in `.env`:  `GOOGLE_CSE_CX=xxxxxxxxxxxx`

8. **Enable Custom Search API + allow it on a key**
   - Enable: https://console.cloud.google.com/apis/library/customsearch.googleapis.com?project=named-sequencer-458710-n1
   - The current `PSI_API_KEY` is **restricted to PSI only**. Either:
     - (a) loosen it: APIs & Services → Credentials → that key → *API restrictions* → add "Custom Search API"; the toolkit will reuse `PSI_API_KEY`. OR
     - (b) make a new key and set `CSE_API_KEY=...` in `.env`.

---

## Verify

```
python audit/seo/check.py
```
Prints PASS/FAIL per capability with the exact fix if anything's missing.

## Use (once green)

```
python audit/seo/gsc.py queries 28          # what people search → suriota
python audit/seo/gsc.py opportunities 28     # page-1-but-not-top-3 quick wins
python audit/seo/gsc.py pages 28             # top landing pages
python audit/seo/gsc.py inspect https://suriota.com/suriota-modbus-gateway/
python audit/seo/gsc.py sitemaps
python audit/seo/ga4.py overview 28
python audit/seo/ga4.py channels 28
python audit/seo/ga4.py landing 28
python audit/seo/indexing.py push https://suriota.com/<page-we-just-fixed>/
python audit/seo/rank.py --file audit/seo/keywords.txt
```

## .env keys this toolkit reads
```
GOOGLE_SA_JSON=        # optional; default audit/seo/sa.json
GSC_SITE=              # optional; default sc-domain:suriota.com
GA4_PROPERTY_ID=       # numeric GA4 property id (required for ga4.py)
GOOGLE_CSE_CX=         # Programmable Search Engine id (required for rank.py)
CSE_API_KEY=           # optional; falls back to PSI_API_KEY
```
