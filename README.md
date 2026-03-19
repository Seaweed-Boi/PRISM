# PRISM — Predictive Income Protection for Gig Workers

## Overview

PRISM is an AI-powered parametric insurance platform designed to protect gig economy delivery workers from **income loss caused by external disruptions** such as weather, traffic congestion, pollution, and platform outages.

Instead of insuring events, PRISM insures **expected earnings**. The system predicts how much a worker should earn and automatically compensates them when real earnings drop due to verified disruptions.

---

## Problem Statement

Delivery partners (Swiggy, Zomato, Amazon, etc.) face unpredictable income loss due to factors outside their control:

* Extreme weather (rain, heat, floods)
* Traffic congestion
* Pollution spikes
* Curfews or local shutdowns
* Platform outages

Currently, there is **no income protection mechanism**, forcing workers to absorb financial losses.

---

## Solution

PRISM provides **parametric income protection** by:

1. Predicting expected earnings using AI
2. Monitoring real-time disruptions
3. Detecting income deviation
4. Automatically triggering payouts

No manual claims. No paperwork.

---

## Key Features

### 1. AI-Powered Risk Assessment

* Predicts expected hourly earnings for each worker
* Calculates zone-based risk scores
* Generates dynamic weekly premiums

### 2. Parametric Claim Automation

* Real-time monitoring of disruption triggers
* Automatic claim initiation when income drops
* Instant payout simulation

### 3. Intelligent Fraud Detection

* GPS-based location validation
* Worker activity verification
* Anomaly detection for suspicious claims

### 4. Multi-Source Data Integration

* Weather APIs
* Traffic data
* Pollution data
* Mock platform activity APIs
* Payment gateway (simulated)

### 5. Analytics Dashboard

**Worker Dashboard**

* Expected earnings
* Protected income
* Active policies
* Payout history

**Admin Dashboard**

* Disruption heatmaps
* Risk distribution
* Claim statistics
* Weekly risk forecasts

---

## How It Works

### Step 1: Onboarding

Worker registers with:

* delivery platform
* working zone
* working hours

System creates a worker profile.

### Step 2: Weekly Policy Purchase

Worker selects a weekly insurance plan based on risk.

Example:

* Low risk → ₹10/week
* Medium risk → ₹20/week
* High risk → ₹35/week

### Step 3: Earnings Prediction

AI model predicts expected earnings (₹/hour) based on:

* time of day
* location
* historical patterns
* external conditions

### Step 4: Disruption Monitoring

System continuously tracks:

* rainfall levels
* traffic congestion
* air quality
* external events

### Step 5: Income Loss Detection

Loss = Expected Earnings − Actual Earnings

If loss exceeds a threshold and a disruption is verified → claim is triggered automatically.

### Step 6: Instant Payout

Compensation is calculated and sent via simulated payment gateway.

---

## Example Scenario

* Expected earnings: ₹700
* Actual earnings: ₹350
* Cause: heavy rainfall

System detects disruption and pays ₹350.

---

## System Architecture

External APIs (Weather, Traffic, Pollution)
→ Disruption Engine
→ AI Risk Model
→ Policy & Claim Engine
→ Fraud Detection
→ Payout System
→ Frontend UI

---

## Tech Stack

### Frontend

* Next.js
* Tailwind CSS
* Mapbox

### Backend

* FastAPI
* PostgreSQL
* Redis

### AI/ML

* Python
* Scikit-learn / XGBoost

### Integrations

* Weather API
* Traffic API
* Mock delivery platform API
* Razorpay / UPI sandbox

---

## AI Components

### Earnings Prediction Model

Predicts expected hourly income using:

* historical delivery data
* time and location features
* environmental factors

### Risk Scoring Model

Calculates weekly risk for pricing:

* weather volatility
* traffic patterns
* disruption frequency

### Fraud Detection Model

Detects anomalies such as:

* GPS spoofing
* inactivity during claims
* repeated suspicious patterns

---

## Weekly Pricing Model

Premium = f(risk_score, zone, disruption_frequency)

Examples:

* Low risk → ₹10/week
* Medium risk → ₹20/week
* High risk → ₹35/week

---

## Demo Flow

1. Worker logs in
2. Buys weekly policy
3. System shows predicted earnings
4. Simulate disruption (e.g., heavy rain)
5. Earnings drop
6. System auto-detects loss
7. Claim triggered
8. Instant payout displayed

---

## Future Enhancements

* Real-time integration with delivery platforms
* Advanced demand prediction models
* Personalized insurance plans
* Multi-city deployment

---

## One-Line Pitch

PRISM protects gig workers by predicting their expected income and automatically compensating them when external disruptions reduce their earnings.
