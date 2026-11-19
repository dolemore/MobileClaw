# MobileClaw — `getmobileclaw.com` & Google Cloud Run ("Build for Good")

Bu klasör tek komutla **Google Cloud Run** üzerine çıkıp hem **`https://getmobileclaw.com`** web sitesini, hem **`https://getmobileclaw.com/privacy`** gizlilik politikasını, hem de eski/düşük RAM'li telefonlar için **`/mcp`** (Model Context Protocol) ve **`/v1/chat/completions`** arka ucunu çalıştırır.

## 1. Tek Komutla Google Cloud Run'a Gönderme
Eve geçtiğinde terminalde şu komutu çalıştır:

```powershell
gcloud run deploy mobileclaw-good --source cloud-run --region europe-west1 --allow-unauthenticated
```

## 2. `getmobileclaw.com` Alan Adını Bağlama (Cloud Run + Spaceship)
1. Google Cloud Console → **Cloud Run → Alan Adı Eşlemeleri (Domain Mappings) → Alan Adı Ekle** → `mobileclaw-good` servisini ve `getmobileclaw.com` adresini seç.
2. Ekranda verdiği `A` / `AAAA` (veya `www` için `ghs.googlehosted.com` `CNAME`) kayıtlarını **Spaceship → Alan Adı Portföyü → getmobileclaw.com → DNS Ayarları** içine yapıştır. (SSL sertifikasını Google Cloud Run otomatik ve ücretsiz üretir.)

## 3. Telefondaki MobileClaw Uygulamasından Bağlama
- **MCP Sunucusu olarak:** MobileClaw → **Ayarlar → MCP Sunucuları** → Adres: `https://getmobileclaw.com/mcp`
- **Düşük RAM'li Eski Telefonlarda AI Sunucusu olarak:** MobileClaw → **Asistan → AI Bağlantısı → Özel Sunucu (OpenAI Uyumlu)** → Base URL: `https://getmobileclaw.com/v1`

---

## 4. Product Hunt x Google Cloud Run (20 Kasım "Build for Good") Hazır Başvuru Metni

- **Name:** MobileClaw
- **Website / Link:** `https://getmobileclaw.com` (veya Google Play linki)
- **Tagline (59/60):** Upcycle any Android phone into an AI elder, kid & car helper
- **Description (255/260):** An Android launcher built for good: turns any phone into a talking memory aid for elders, a Socratic study coach for kids, and a car cockpit + dashcam for old cars. Runs offline via LiteRT-LM/llama.cpp, or scales to zero on Google Cloud Run for old 2GB phones.
- **First Comment / Architecture Deep-Dive (Maker Comment):**

> Hi Product Hunt & Google Cloud Run team! 👋
>
> I built **MobileClaw** (`com.la1ncher`) to solve a simple "Build for Good" problem: millions of older Android phones sit forgotten in drawers while families need affordable assistive tech for older relatives, distraction-free study tools for kids, and safety screens for older cars without CarPlay/Android Auto.
>
> **How it helps people (Build for Good):**
> 1. **Elder Care & Talking Memory Aid (`Simple Mode`):** Large high-contrast controls, a one-tap family call button, spoken daily/medication reminders, and a calm talking memory assistant.
> 2. **Kid Socratic Study Coach (`Kid Mode`):** Guides children through math, reading, and spelling step by step with Socratic questions instead of handing over homework answers—behind a parent PIN, with zero ads and zero child tracking.
> 3. **E-Waste Upcycling (`Car Cockpit & Dashcam`):** Turn an old phone sideways on a car mount for a full-screen map with turn-by-turn directions, big media controls, and a loop-recording road/cabin dashcam with live PiP and crash-shock file locking.
>
> **Deep Dive — Hybrid On-Device + Google Cloud Run Architecture:**
> - **Tier 0 (Deterministic On-Device Rules):** Time, battery, alarms, DND, and plain-sentence automations execute in <5 ms with zero RAM overhead.
> - **Tier 1 (On-Device LLM for 6GB+ phones):** Runs `.litertlm` models on the GPU via Google's **LiteRT-LM** (`Gemma 4 E2B`, `EmbeddingGemma 270M`) and `.gguf` models on the CPU via **llama.cpp** with `Q8_0` quantized KV cache and instant unload on Android's `onTrimMemory`.
> - **Tier 2 (Google Cloud Run Bridge for 2–4GB Upcycled Drawer Phones):** Old phones in a drawer don't have 4 GB of free RAM to hold weights in memory. They connect over HTTPS to our stateless, scale-to-zero **Google Cloud Run** service (`https://getmobileclaw.com`), which exposes:
>   - `POST /mcp` (**Model Context Protocol JSON-RPC 2.0**): Exposes `socratic_study_hint`, `elder_care_checkin`, and `recent_earthquakes` (live USGS seismic safety check) directly to the phone's 6-step ReAct agent loop.
>   - `POST /v1/chat/completions`: Stateless Cloud Run inference relay so a 7-year-old 2 GB phone can still power the talking elder memory aid and Socratic tutor with zero local RAM pressure and $0 idle cost when nobody is asking a question.
>
> Live on Google Play: https://play.google.com/store/apps/details?id=com.la1ncher
> Cloud Run Service & Architecture: https://getmobileclaw.com
