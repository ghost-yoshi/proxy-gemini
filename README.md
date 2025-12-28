# 🔮 Gemini Proxy API (FastAPI)

API intermédiaire sécurisée pour utiliser **Google Gemini** sans exposer la clé API côté client (bot WhatsApp, scripts, apps, etc.).

👉 Le bot envoie une requête à cette API  
👉 L’API appelle Gemini  
👉 Le bot reçoit uniquement la réponse (JSON)

---

## 🚀 Fonctionnalités

- 🔐 Clé **Gemini stockée uniquement côté serveur**
- 🧠 Utilise **Gemini 2.5 Flash**
- 🔑 Authentification simple par token
- ⚡ Léger, rapide, scalable
- 🌐 Déployable sur **Vercel**

---

## 🧱 Architecture


service
↓
[ Gemini Proxy API ]
↓
Google Gemini API


---

## 📦 Installation locale

### 1️⃣ Cloner le projet
```bash
git clone https://github.com/ghost-yoshi/gemini-proxy.git
cd gemini-proxy

pip install -r requirements.txt
