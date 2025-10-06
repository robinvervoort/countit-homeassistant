# 🧾 Count-It for Home Assistant

**Count-It** is a custom integration for [Home Assistant](https://www.home-assistant.io)  
that connects to your [Count-It.eu](https://start.count-it.eu) account to fetch daily, weekly, monthly, and yearly sales data — including product lists and customer counts.

---

## ✨ Features

- 📈 Sales metrics (Day, Week, Month, Year)
- 🛍️ Sold products list (as sensor attributes)
- 👥 Customer count
- ⚙️ Scraper status binary sensor
- 🔁 Configurable update interval & timeout
- 🔐 Multiple Count-It accounts supported

---

## 🧩 Installation (via HACS)

1. In **HACS → Integrations**, click **⋮ → Custom repositories**
2. Add this repository:  
   `https://github.com/robinvervoort/countit-homeassistant`
3. Choose category: `Integration`
4. Search **Count-It** → **Download**
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration → Count-It**

---

## ⚙️ Configuration

When adding the integration:
- Enter your Count-It **username** and **password**
- Give this account a **display name**
- Optionally adjust:
  - Update interval (minutes)
  - Timeout (seconds)
- Data is refreshed automatically.

---

## 📊 Exposed Entities

| Entity ID | Description | Unit |
|------------|--------------|------|
| `sensor.countit_daily_sales` | Daily turnover | € |
| `sensor.countit_weekly_sales` | Weekly turnover | € |
| `sensor.countit_monthly_sales` | Monthly turnover | € |
| `sensor.countit_yearly_sales` | Yearly turnover | € |
| `sensor.countit_customers` | Number of customers | count |
| `sensor.countit_products` | List of sold products (attribute) | items |
| `binary_sensor.countit_scraper_status` | Shows scraper OK/error | bool |

---

## 🧠 Notes
- Products are parsed from Count-It PDF exports.
- Integration handles multiple departments per account.
- Data updates every 15 minutes by default.

---

## 🧑‍💻 Author
Developed by **Robin Vervoort**