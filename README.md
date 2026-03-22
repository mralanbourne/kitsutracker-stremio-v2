<p align="center">
  <img src="https://kitsutracker.koyeb.app/static/fox.png" width="300" alt="Kitsu Logo">
</p>

<h1 align="center">Kitsu Tracker for Stremio V2</h1>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/Stremio-Addon-8a5a9e?style=for-the-badge&logo=stremio" alt="Stremio Addon">
  <img src="https://img.shields.io/badge/Status-Online-success?style=for-the-badge" alt="Status Online">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License MIT">
  <img src="https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white" alt="Docker Ready">
</p>

<p align="center">
  <strong>The definitive, high-performance bridge between Stremio and Kitsu. Sync your watch progress automatically and access your personal catalogs with ease.</strong>
</p>

<div align="center">
  <h3>🌐 Community Instance</h3>
  <a href="https://kitsutracker.koyeb.app">kitsutracker.koyeb.app</a>
  <br />
  <br />
  <a href="https://kitsutracker.koyeb.app">
    <img src="https://img.shields.io/badge/INSTALL_NOW-CLICK_HERE-FD755C?style=for-the-badge&logo=rocket" alt="Install Button" height="55">
  </a>
</div>

---

> [!WARNING]
> ### 🔒 Privacy & Security Notice
> Kitsu currently lacks standard OAuth2 for third-party apps, meaning you need to log in directly via this interface. I take your data security very seriously:
>
> * **Zero Password Storage:** Your password is strictly used **once** to generate a secure Kitsu access token. It is never stored in the database or logged anywhere.
> * **Secure Client Sessions:** Only your non-sensitive Kitsu User ID is cryptographically signed and stored locally in your browser. All sensitive refresh tokens are completely isolated and secured in the backend database.
> * **Minimal Data:** Only your Kitsu ID, generated tokens, and watch progress are stored to facilitate synchronization.
> * **100% Open Source:** Don't trust, verify! The entire architecture is public.

### ✨ Features
* **⚡ Auto-Tracking:** Your episode progress updates automatically on Kitsu in the background the moment you press play.
* **🔄 Auto-Healing Sessions:** Your Kitsu access tokens are automatically refreshed in the background before they expire, ensuring your tracking never drops out mid-binge.
* **🔍 Native Kitsu Search:** Search for anime directly through the addon to ensure Stremio uses proper kitsu: IDs.
* **📂 Personal Catalogs:** Browse your Kitsu lists (Watching, Planned, Completed, etc.) directly as native Stremio rows.
* **🚀 High Performance:** Powered by a fully asynchronous Quart engine, robust API retry logic, and an Upstash Redis backend for lightning-fast catalog loading.

### 🦊 Quick Start
1. **Login:** Open the [Community Instance](https://kitsutracker.koyeb.app) and sign in with your Kitsu account.
2. **Setup:** Choose which catalogs you want to see in Stremio and click Save.
3. **Install:** Use the Install button on the dashboard to add the addon to Stremio.

> [!IMPORTANT]
> **Tracking New Anime:** To ensure a new anime is added to your Kitsu list automatically, search for it in Stremio and select the result under the "Kitsu: Search" category.
> 
> **Syncing Note:** Stremio caches catalogs aggressively. It can take up to 5 minutes for list changes to visually update on your home screen. (changes on Kitsu are instant though😘) 

---

<details>
<summary>💻 <strong>Self-Hosting Instructions (Developers)</strong></summary>

### How to host your own instance
V2 is fully Dockerized and optimized for modern PaaS environments using an asynchronous ASGI server (Hypercorn). It utilizes a connectionless HTTP REST approach via Upstash Redis.

#### 1. Prerequisites
* **Upstash Redis:** Create a free serverless Redis database on [Upstash](https://upstash.com).
* **Kitsu API Keys:** Extract client keys from the official web app:
  1. Open [Kitsu](https://kitsu.app/)
  2. Open Developer Tools (F12) -> Network tab and log in.
  3. Look for a request named token ```https://kitsu.io/api/oauth/token```.
  4. Find ```client_id``` and ```client_secret``` in the request payload.

#### 2. Deployment (Docker)
1. **Clone the Repo:** 
``` git clone https://github.com/mralanbourne/kitsutracker-stremio-v2.git```
and then ```cd kitsutracker-stremio-v2```
<br>

2. **Build and Run:**
``` docker build -t kitsutracker
docker run -p 8000:8000 \
  -e UPSTASH_REDIS_REST_URL="your_url" \
  -e UPSTASH_REDIS_REST_TOKEN="your_token" \
  -e SECRET_KEY="random_string" \
  -e KITSU_CLIENT_ID="your_id" \
  -e KITSU_CLIENT_SECRET="your_secret" \
  kitsutracker
```
3. **Cloud Deployment (e.g., Koyeb)**

Koyeb will automatically detect the Dockerfile in the root directory.

    Port: Ensure the port is set to 8000 in your service settings.

    Environment Variables: Add all variables listed in the example above to your environment configuration.

</details>
☕ Support

I'm hosting this instance for free for the community. If you find this service useful, consider supporting the development!
<p align="center">
<a href="https://ko-fi.com/mralanbourne" target="_blank">
<img src="https://storage.ko-fi.com/cdn/kofi2.png?v=3" height="40" alt="Buy Me a Coffee at ko-fi.com" />
</a>

<p align="center">
Made with ❤️ for the Anime Community.
<p align="center">
<sub>Based on the architecture of <a href="https://github.com/SageTendo/mal-stremio-addon">MAL-Stremio Addon</a> by SageTendo.</sub>
</p>
