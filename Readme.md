# EcoSort AI: AI-Powered Smart Waste Segregation & Recycling Assistant

## 1M1B AI for Sustainability Virtual Internship — Final Project

---

## SECTION 1: PROJECT OVERVIEW

### Project Title

**EcoSort AI — AI-Powered Smart Waste Segregation & Recycling Assistant for Sustainable Cities**

### Team Details

- **Name:** Banish J, Ashika, Catherine, Raja
- **Institution:** NI University
- **Submission Date:** June 2026

### SDG Alignment

| SDG        | Goal                                   | Connection to Project                                                                    |
| ---------- | -------------------------------------- | ---------------------------------------------------------------------------------------- |
| **SDG 11** | Sustainable Cities and Communities     | Primary — Reduces urban waste mismanagement, promotes recycling infrastructure in cities |
| **SDG 12** | Responsible Consumption and Production | Secondary — Educates citizens on proper disposal and recycling habits                    |
| **SDG 13** | Climate Action                         | Tertiary — Reduces methane emissions from landfills through better segregation           |

### Problem Statement

> **"How might we use AI to help urban citizens and municipal workers segregate waste correctly so that our cities can become more sustainable and reduce landfill burden?"**

### The Problem (Context)

In Indian urban cities, over **62 million tonnes of waste** is generated annually, but only about **30% is properly treated**. The rest ends up in landfills. Key challenges include:

- **Lack of awareness**: Citizens don't know how to segregate waste (wet, dry, hazardous, recyclable)
- **Inconsistent municipal systems**: Waste collectors receive mixed waste, making recycling impossible
- **Health hazards**: Improper disposal of e-waste, batteries, and hazardous materials
- **Environmental damage**: Landfills produce methane and leachate, polluting air and groundwater

### The Solution (EcoSort AI)

EcoSort AI is a conceptual AI-powered assistant that helps users:

1. **Identify waste types** using image recognition (photo of waste item)
2. **Learn correct disposal methods** through an AI chatbot with RAG-powered knowledge base
3. **Get location-specific guidance** on nearby recycling centers and collection schedules
4. **Track their environmental impact** — showing how much waste they've diverted from landfills

---

## SECTION 2: AI SOLUTION OVERVIEW

### Architecture Overview

```
                    ┌─────────────────────────────────────────┐
                    │            USER INTERFACE                │
                    │  (Mobile App / WhatsApp Bot / Web App)   │
                    └──────────────┬──────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────────┐
                    │         ORCHESTRATOR AGENT               │
                    │  (IBM Agentic AI — Routes & Coordinates) │
                    └──────┬─────────────┬──────────┬─────────┘
                           │             │          │
              ┌────────────▼──┐  ┌───────▼──────┐ ┌─▼────────────┐
              │  CLASSIFIER   │  │  RAG ENGINE  │ │  LOCATION    │
              │   AGENT       │  │   AGENT      │ │  AGENT       │
              │  (IBM Granite)│  │ (Knowledge)  │ │ (Mapping)    │
              └───────────────┘  └──────────────┘ └──────────────┘
```

### AI Components Used

#### 1. IBM Granite Model — Waste Classification

- **Role**: Classifies waste items from user descriptions or image analysis
- **Input**: User text description OR image of waste item
- **Output**: Waste category (Organic, Plastic, Metal, Glass, Paper, E-waste, Hazardous, etc.)
- **Technique**: Prompt engineering with few-shot examples + entity extraction

#### 2. Retrieval-Augmented Generation (RAG) — Knowledge Base

- **Role**: Provides accurate disposal guidelines, recycling facts, and local rules
- **Source Documents**: Municipal waste management guidelines, CPCB (Central Pollution Control Board) rules, recycling best practices
- **Process**:
  1. User asks a disposal question
  2. Query is embedded and searched against vector database
  3. Relevant chunks retrieved
  4. IBM Granite generates answer grounded in retrieved context

#### 3. Agentic AI Workflow — Multi-Agent Orchestration

- **Role**: Coordinates multiple specialized sub-agents for end-to-end assistance
- **Agents in the workflow**:
  - *Classifier Agent* — Identifies the waste type
  - *RAG Agent* — Retrieves disposal instructions
  - *Location Agent* — Finds nearby recycling centers
  - *Impact Tracker Agent* — Calculates environmental impact
  - *Supervisor Agent* — Coordinates and responds to user

### Target Users

| User Group              | How They Use EcoSort AI                                                 |
| ----------------------- | ----------------------------------------------------------------------- |
| **Urban Households**    | Snap a photo of waste before disposal, get instant segregation guidance |
| **Municipal Workers**   | Quick verification tool at collection points                            |
| **Local Businesses**    | Bulk waste disposal guidance and recycling partner connection           |
| **Students & Citizens** | Learn about recycling through the interactive chatbot                   |

---

## SECTION 3: PROMPT ENGINEERING & RAG PIPELINE DESIGN

### 3.1 Prompt Engineering — Waste Classifier

**System Prompt:**

```
You are EcoSort AI, a waste classification assistant powered by IBM Granite.
Your task is to classify waste items into one of these categories:
1. Organic / Biodegradable (food scraps, garden waste, paper)
2. Recyclable (plastic bottles, metal cans, glass, cardboard)
3. Hazardous (batteries, paint, chemicals, medical waste)
4. E-waste (electronics, wires, circuit boards)
5. Reject / Landfill (tissue paper, ceramic, mixed materials)

For each item, provide:
- Category
- Brief reason
- Disposal instruction (1 sentence)
- A safety note if applicable
```

**Few-Shot Example (User → Assistant):**

```
User: "I have a used plastic water bottle."

Assistant:
- Category: Recyclable (Plastic)
- Reason: PET plastic bottles are 100% recyclable
- Disposal: Rinse and place in the dry/recyclable waste bin
- Safety: Ensure bottle is empty before disposal
- Did You Know? One recycled plastic bottle saves enough energy to power a 60W bulb for 6 hours!

---

User: "I have an old mobile phone that doesn't work."

Assistant:
- Category: E-waste
- Reason: Mobile phones contain precious metals and hazardous materials
- Disposal: Do NOT throw in regular bin. Take to an authorized e-waste collection center
- Safety: Lithium-ion batteries can cause fires if crushed. Remove battery if possible.
- Did You Know? 1 ton of recycled phones yields more gold than 1 ton of gold ore!
```

### 3.2 RAG Pipeline Design

```
Step 1: INGESTION
  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
  │ Source Docs  │───▶│ Chunking     │───▶│ Embeddings   │
  │ (PDFs, PDFs) │    │ (500 chars)  │    │ (Vector DB)  │
  └─────────────┘    └──────────────┘    └──────────────┘
  - CPCB Guidelines     - Overlap: 50    - IBM Granite
  - Municipal Rules       chars            Embeddings
  - Recycling Guides

Step 2: RETRIEVAL (When user asks a question)
  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │ User Query   │───▶│ Embed Query  │───▶│ Semantic     │
  │ "How to      │    │              │    │ Search (Top 3)│
  │  dispose     │    │              │    │              │
  │  batteries?" │    │              │    │              │
  └──────────────┘    └──────────────┘    └──────────────┘

Step 3: GENERATION
  ┌──────────────────┐    ┌──────────────────┐
  │ Retrieved Chunks │───▶│ IBM Granite      │──▶ Answer
  │ + Original Query │    │ (RAG Prompt)     │
  └──────────────────┘    └──────────────────┘
```

**RAG Prompt Template:**

```
You are an AI waste management assistant. Use ONLY the following
information to answer the user's question. If the information
doesn't contain the answer, say "I don't have specific information
about that in my knowledge base."

Context:
{retrieved_chunks}

User Question: {user_query}

Answer the question clearly and concisely. Include a tip if relevant.
```

### 3.3 Sample RAG Interactions

**User Query:** "How should I dispose of used cooking oil?"
**Retrieved Chunks:**

1. "Used cooking oil should never be poured down the drain as it causes pipe blockages and pollutes water bodies"
2. "Collect cooled oil in a sealed container and drop at designated collection points"
3. "Some municipalities partner with biodiesel companies that accept used oil"

**Generated Answer:**

> Used cooking oil should NEVER be poured down the sink. Let it cool, pour it into a sealed bottle, and drop it at your nearest used oil collection center. Many cities now have biodiesel partners who convert this oil into fuel!
> 
> *Tip: One litre of used oil can contaminate 1 million litres of water — proper disposal matters!*

---

## SECTION 4: AGENTIC AI WORKFLOW

### 4.1 Full Agentic Workflow

```
                      USER INPUT
                  (Text / Image / Voice)
                         │
                         ▼
              ┌─────────────────────┐
              │   SUPERVISOR AGENT  │
              │  (IBM Agentic AI)   │
              │  - Intent Detection │
              │  - Task Routing     │
              └──┬──────┬──────┬───┘
                 │      │      │
    ┌────────────▼┐ ┌───▼────┐ ┌▼────────────┐
    │CLASSIFY     │ │RAG     │ │LOCATION     │
    │AGENT        │ │AGENT   │ │AGENT        │
    │             │ │        │ │             │
    │- Granite    │ │- Vector│ │- Maps API   │
    │  classification│ Search │ │- Nearby     │
    │- Category   │ │- Answer│ │  centers    │
    │  + reason   │ │  gen   │ │- Schedule   │
    └──────┬──────┘ └───┬────┘ └──────┬──────┘
           │            │             │
           └────────────┼─────────────┘
                        ▼
              ┌─────────────────────┐
              │    IMPACT TRACKER   │
              │    AGENT            │
              │  - CO2 saved calc   │
              │  - Landfill divert  │
              │  - Streak tracking  │
              └─────────┬──────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │   FINAL RESPONSE    │
              │  (Supervisor compiles│
              │   all agent outputs) │
              └─────────────────────┘
```

### 4.2 Agent Interaction Example

**User:** "I have a broken laptop. What should I do?"

| Step | Agent              | Action         | Output                                                              |
| ---- | ------------------ | -------------- | ------------------------------------------------------------------- |
| 1    | **Supervisor**     | Detect intent  | "Waste classification + disposal guidance needed"                   |
| 2    | **Classifier**     | Classify       | **E-waste** (laptop — electronic device)                            |
| 3    | **RAG Agent**      | Retrieve rules | "e-waste rules under E-Waste Management Rules 2022"                 |
| 4    | **Location Agent** | Find centers   | "3 e-waste collection centers within 2km of your location"          |
| 5    | **Impact Tracker** | Calculate      | "Recycling this laptop saves 240kg of CO2 vs. mining raw materials" |
| 6    | **Supervisor**     | Compile        | Final user-friendly response                                        |

**Final Response Generated by Supervisor:**

```
🖥️ Your broken laptop is classified as E-WASTE.

📋 IMPORTANT: Do NOT throw it in the regular bin.
E-waste contains hazardous materials that must be handled properly.

📍 Nearby Collection Centers:
1. GreenEco Recyclers — 1.2 km away (Open 9 AM-6 PM)
2. City E-Waste Hub — 1.8 km away (Free drop-off)
3. TechRecycle Kiosk — 2.5 km away (Also offers pickup)

🌍 Your Impact: Recycling this laptop saves ~240 kg CO2
— equivalent to planting 12 trees!

💡 Tip: Remember to wipe your hard drive before disposal!
```

---

## SECTION 5: PROTOTYPE / DEMO

### 5.1 Sample User Flow

```
SCREEN 1: HOME
┌─────────────────────────────┐
│  🌱 EcoSort AI              │
│                             │
│  [📷 Snap a Photo]          │
│  [💬 Ask the Assistant]     │
│  [📍 Find Recycling Center] │
│                             │
│  Your Impact So Far:        │
│  🎯 12 kg waste diverted    │
│  🌿 8.5 kg CO₂ saved        │
└─────────────────────────────┘


SCREEN 2: CLASSIFICATION RESULT
┌─────────────────────────────┐
│  📸 Photo Analyzed          │
│                             │
│  Item: Plastic Water Bottle │
│  ┌─────────────────────┐    │
│  │   ♻️ RECYCLABLE     │    │
│  └─────────────────────┘    │
│                             │
│  ✅ Rinse and place in      │
│     dry waste / recycling   │
│                             │
│  🌍 1 bottle recycled =     │
│     6 hours of bulb power   │
│                             │
│  [📍 Find Nearest Bin]      │
│  [💡 Learn More]            │
└─────────────────────────────┘


SCREEN 3: CHAT ASSISTANT
┌─────────────────────────────┐
│  💬 Ask EcoSort             │
│                             │
│ ┌─────────────────────────┐ │
│ │ How do I dispose        │ │
│ │ expired medicines?      │ │
│ └─────────────────────────┘ │
│                             │
│ EcoSort:                    │
│ ⚠️ HAZARDOUS WASTE          │
│                            │
│ Medicines should NOT be    │
│ flushed or thrown in       │
│ regular trash.             │
│                            │
│ ✅ Return to pharmacy      │
│ ✅ Use drug take-back box  │
│                            │
│ 📍 2 pharmacies near you   │
│    accept expired meds     │
└─────────────────────────────┘
```

### 5.2 Sample Input → Output Demonstrations

**Demo 1: Text Classification**

| Input                             | Output                                                                               |
| --------------------------------- | ------------------------------------------------------------------------------------ |
| "I have banana peels"             | **Organic** → Compost or green bin. Great for your garden!                           |
| "Where do I throw glass bottles?" | **Recyclable (Glass)** → Rinse and drop in glass recycling. 100% recyclable forever! |
| "Old paint cans"                  | **Hazardous** → Never in regular trash. Take to hazardous waste facility.            |

**Demo 2: RAG Query**

| User Question                                               | AI Response                                                                                                                                                                                         |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "What is the penalty for not segregating waste in my city?" | *[Retrieved from municipal rules]* "As per your city's Solid Waste Management bylaws, households can be fined ₹200-₹500 for not segregating waste at source."                                       |
| "Can I recycle pizza boxes?"                                | *[Retrieved from recycling guidelines]* "Only CLEAN cardboard is recyclable. If the pizza box has grease stains, the soiled parts should go in organic waste. Cut out the clean lid for recycling!" |

---

## SECTION 6: IMPACT STATEMENT

### Environmental Impact (If Implemented)

| Metric                           | Current Situation         | With EcoSort AI (Projected)      |
| -------------------------------- | ------------------------- | -------------------------------- |
| Waste reaching landfills         | ~70% of urban waste       | Reduced to ~40%                  |
| Recycling rate                   | ~30%                      | Increased to ~60%                |
| Methane emissions from landfills | High (3rd largest source) | Significant reduction            |
| Citizen awareness                | Very low                  | High — via interactive education |
| Hazardous waste properly treated | ~15%                      | ~50%+                            |

### Social Impact

- **Empowers citizens** with knowledge to make sustainable choices
- **Protects waste workers** from hazardous materials by reducing improper disposal
- **Creates green jobs** in recycling ecosystem
- **Reduces health costs** from pollution-related diseases

### Alignment with Indian Government Initiatives

- **Swachh Bharat Mission 2.0**: Directly supports urban waste management goals
- **Circular Economy**: Promotes recycling and resource recovery
- **LiFE Movement (Lifestyle for Environment)**: Encourages sustainable daily habits

---

## SECTION 7: RESPONSIBLE AI CONSIDERATIONS

### 7.1 Fairness

- **Challenge**: AI might misclassify items from lower-income households (e.g., informal waste)
- **Mitigation**: Train on diverse waste types across income groups; regular bias audits
- **Inclusive Design**: Support multiple Indian languages (Hindi, regional languages) via text and voice

### 7.2 Transparency

- **Explainability**: Every classification includes a clear reason ("Why this is recyclable")
- **Confidence Levels**: Show when AI is uncertain ("I'm 70% sure this is plastic — please verify")
- **Limitations**: Clearly communicate what the AI can and cannot do

### 7.3 Privacy & Data Security

- **Image Handling**: User photos are processed and deleted — NOT stored
- **Location Data**: Used only for finding nearby centers; opt-in required
- **No Personal Tracking**: User identity is anonymous; no personal data sold or shared
- **GDPR / DPDP Act Compliance**: Follows India's Digital Personal Data Protection Act 2023

### 7.4 Accountability

- **Human Oversight**: Final disposal decisions always rest with the user
- **Feedback Loop**: Users can correct misclassifications to improve the model
- **Escalation**: Hazardous waste classifications include verification prompts

### 7.5 Environmental Responsibility of AI Itself

- **Model Efficiency**: Uses smaller, fine-tuned models (IBM Granite) instead of massive LLMs to reduce compute energy
- **Edge Deployment**: Classification can run on-device for common items, saving cloud energy

### 7.6 Ethical Considerations

- **No Greenwashing**: Impact metrics are scientifically calculated and cited
- **Equitable Access**: Free tier ensures low-income households are not excluded
- **Worker Protection**: Designed to help, not replace, municipal waste workers

---

## SECTION 8: TECHNOLOGY STACK SUMMARY

| Component                 | Technology                                | Purpose                                |
| ------------------------- | ----------------------------------------- | -------------------------------------- |
| **AI Model**              | IBM Granite Model (via watsonx)           | Waste classification & text generation |
| **RAG**                   | Embeddings + Vector Database (watsonx.ai) | Knowledge retrieval for disposal rules |
| **Agentic AI**            | IBM Agentic AI Framework                  | Multi-agent orchestration              |
| **Development**           | Google Colab / IBM watsonx                | Model experimentation & prototyping    |
| **AI Assistance**         | IBM BOB                                   | Assisted code & workflow development   |
| **Frontend (Conceptual)** | Mobile App / WhatsApp API / Web           | User interface                         |
| **Mapping**               | OpenStreetMap / Google Maps API           | Location-based recycling center finder |

---

## SECTION 9: CONCLUSION

EcoSort AI demonstrates how Artificial Intelligence — specifically IBM Granite Models, Retrieval-Augmented Generation, and Agentic AI workflows — can address one of the most pressing urban sustainability challenges: **waste mismanagement**.

By combining:

- 🧠 **AI Classification** to identify waste
- 📚 **RAG-powered knowledge** to educate users
- 🤖 **Agentic coordination** to provide end-to-end assistance

...EcoSort AI empowers citizens to become active participants in building **Sustainable Cities and Communities (SDG 11)**.

The project is designed with **Responsible AI** (IBM Granite) at its core — ensuring fairness, transparency, privacy, and accountability. It requires no advanced coding to conceptualize, focusing instead on **logic, workflow design, and real-world impact** — exactly as the 1M1B internship envisions. andThis Project is made by Banish J a lead primary Developer

---

*"Small actions, multiplied by millions of people, can transform the world."*
— EcoSort AI

---
