# 📍 LeadMapper — Google Maps Lead Extractor

A premium, full-stack application for extracting business leads from Google Maps. Automate your sales pipeline by gathering names, phone numbers, social handles, and websites in real-time.

---

## 🚀 How It Works

LeadMapper uses **Playwright** to automate a headless browser that navigates through Google Maps search results. It scrolls through the results list, identifies business listings, and then visits each listing individually to scrape deep data points.

### Key Features:
- **Real-time Streaming**: Results appear on your dashboard instantly as they are found.
- **Smart Deduplication**: Prevents duplicate leads using a unique hash of Name + Phone + Website.
- **Rich Data**: Extracts Name, City, Phone (with WhatsApp links), Instagram, Website, and About info.
- **Export Options**: Download as a professionally formatted Excel file or sync directly to Google Sheets.
- **Adjustable Speed**: Control the scraping speed to stay under the radar of anti-bot systems.

---

## 📥 Getting Started

### 1. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/your-repo/leads-extractor.git
cd leads-extractor
```

### 2. Install Dependencies
You need **Python 3.10+** installed on your system.

#### **On Windows:**
```powershell
# Install Python packages
py -m pip install -r backend/requirements.txt

# Install Playwright browsers
py -m playwright install chromium --with-deps
```

#### **On macOS / Linux:**
```bash
# Install Python packages
python3 -m pip install -r backend/requirements.txt

# Install Playwright browsers
python3 -m playwright install chromium
```

---

## 🏗️ Running the Application

To run the application, you need to start the **Backend API** and the **Frontend Dashboard** simultaneously.

### **Windows Instructions**
1. **Start Backend**:
   ```powershell
   cd backend
   py main.py
   ```
2. **Start Frontend** (In a new terminal):
   ```powershell
   cd frontend
   py -m http.server 5500
   ```
   *Open [http://localhost:5500](http://localhost:5500) in your browser.*

### **macOS / Linux Instructions**
1. **Start Backend**:
   ```bash
   cd backend
   python3 main.py
   ```
2. **Start Frontend** (In a new terminal):
   ```bash
   cd frontend
   python3 -m http.server 5500
   ```
   *Open [http://localhost:5500](http://localhost:5500) in your browser.*

---

## 📊 Using the Dashboard

1. **Enter Maps URL**: Go to [Google Maps](https://www.google.com/maps), search for something (e.g., "Software Companies in Bangalore"), and copy the URL from your browser's address bar.
2. **Launch**: Paste the URL into the "Google Maps Search URL" field and click **Start Extraction**.
3. **Live Results**: The table will begin to populate. 
   - Use the 📞 icon to trigger a phone call.
   - Use the 💬 icon to send a WhatsApp message.
   - Add custom notes directly in the "Notes" column (they auto-save to the backend).
4. **Export**: Once finished, click **Download Excel** to get your leads in a structured `.xlsx` file.

---

## ⚙️ Google Sheets Integration (Optional)

1. Create a Google Cloud project and enable **Google Sheets/Drive APIs**.
2. Download your **Service Account JSON** and rename it to `service_account.json`.
3. Place this file in the `backend/` folder.
4. Share your Google Sheet with the service account email.
5. Enter the Sheet URL in the dashboard and click **Push to Google Sheets**.

---

## 🐳 Docker Setup (Cross-Platform)

If you prefer using Docker:
```bash
docker-compose up --build
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)

---

## 🛡️ Best Practices
- **Scroll Delay**: Keep the delay above 1.5s for stability.
- **Max Results**: Set a limit for very large searches to manage memory.
- **Headless Mode**: By default, it runs headless. You can toggle this in `backend/scraper/maps_scraper.py` for debugging.
