# AEGIS

**AI-Based Deployment Risk Prediction Platform**

AEGIS is a platform that analyzes deployment environments and predicts potential risks before software deployments occur.
It integrates with CI/CD tools and infrastructure systems to monitor deployments and provide intelligent insights.

---

## 🚀 Features

* Deployment risk prediction using intelligent analysis
* Environment monitoring
* CI/CD integrations
* Alert system for risky deployments
* Insights dashboard for deployment analytics

---

## 🛠 Tech Stack

### Backend

* Python
* FastAPI
* SQLAlchemy

### Frontend

* Next.js
* TypeScript

### DevOps

* Docker
* Docker Compose

---

## 📂 Project Structure

```
AEGIS
│
├── backend
│   └── app
│       ├── models
│       ├── routers
│       ├── schemas
│       └── services
│
├── Frontend
│   ├── src
│   └── public
│
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## ⚙️ Running the Project

### 1️⃣ Backend

```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend will run on:

```
http://localhost:8000
```

---

### 2️⃣ Frontend

```
cd Frontend
npm install
npm run dev
```

Frontend will run on:

```
http://localhost:3000
```

---

## 📊 Future Improvements

* Machine learning model for deployment risk scoring
* Real-time infrastructure monitoring
* Advanced analytics dashboard
* Cloud provider integrations

---

## 👨‍💻 Author

Vishwas Desai

