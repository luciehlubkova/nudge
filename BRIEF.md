# Nudge – Product Brief

## Přehled
Mobilní web aplikace pro správu osobních úkolů s prioritizací a notifikacemi. Zaměření na **jednoduchost** a **rychlý input** přes braindump view.

---

## Funkční požadavky

### 1. Data model – Task properties

**Povinná pole:**
- **Název** ⭐ (text) – musí být vyplněno
- **Časová náročnost** ⭐ (select): 5 min | 15 min | 60 min | 90 min+ – musí být vybrána
- **Kategorie** ⭐ (select + možnost přidat novou) – musí být vybrána nebo vytvořena

**Volitelná pole:**
- **Popis/Poznámky** (textarea)
- **Termín splnění** (datetime, optional) – nemusí být uveden
- **URL** (optional, text)
- **Fotka/Screenshot** (optional, file upload)
- **Reminder** (datum + čas) – kdy má vyskočit notifikace (samostatné od deadlinu)
- **Opakování** (select): Žádné | Každý měsíc | Každý týden | Každý den

**Status:**
- Aktivní / Archivovaný – při označení checkboxem se task přesune do archivu
- Archivované úkoly jsou stále dostupné pro vyhledání/obnovení

---

### 2. Views – 5 perspektiv
1. **Braindump** (default)
   - Fokus na rychlý input nových úkolů
   - Formulář v horní části (název, čas, kategorie + povinné)
   - Pod formulářem seznam AKTIVNÍCH úkolů (bez filtrování)
   - Ideální pro daily review

2. **Podle náročnosti** (Time-grouped)
   - Úkoly seskupeny: 5 min | 15 min | 60 min | 90 min+
   - Počet úkolů per kategorie
   - Use case: "Co mám času?"

3. **Podle kategorie** (Category-grouped)
   - Úkoly seskupeny podle kategorií (včetně custom)
   - Počet úkolů per kategorie
   - Use case: "Dnes se zaměřím na..."

4. **Podle termínu** (Timeline)
   - Úkoly řazeny vzestupně podle deadlinu (jen s deadlinem)
   - Dnes | Tento týden | Příští týden | Později
   - Use case: "Co je kritické?"

5. **Archiv**
   - Všechny archivované úkoly
   - Možnost obnovení (unarchive)
   - Search/filter v archivu

---

### 3. Interakce
- **Vytvoření úkolu** → libovolný view, priority braindump
  - Povinná pole validace: název + čas + kategorie
  - Možnost přidat novou kategorii přímo z formuláře
- **Editace** → kliknutí na úkol → modal/slide-in form se všemi poli
- **Označení jako splněno** → checkbox → task se archivuje
  - Pokud má opakování → automaticky vytvoř nový úkol s datem +1 měsíc/týden/den
  - Pokud bez opakování → archivován (stále vyhledatelný)
- **Archiv** → vlastní view pro archivované tasky, s možností obnovení
- **Notifikace** → push notification v čase a datu určeném v poli "Reminder"
  - Reminder je nezávislý na deadlinu
  - Lze nastavit libovolný čas (např. den předem, 2 hodiny předem, apod.)

---

### 4. UI Design – 3 návrhy (Zemitá paleta barev)

**Barvy (přiložená paleta):**
```
Světlé tóny: #F7E6CA (cream), #E8D59E (sand), #FFD3AC (peach), #F5F5DC (ivory)
Neutrály: #CCBEB1 (warm gray), #898989 (gray), #D9BBB0 (mauve)
Hnědé tóny: #AD9C8E (taupe), #6F4E37 (brown), #664C36 (dark brown), #331C08 (very dark)
Akcentní: #D47E30 (orange), #4B6E48 (green), #B2AC88 (olive)
```

#### **Návrh A: Minimalistický (Calm)**
- Background: #F5F5DC (ivory)
- Primární text: #331C08 (very dark brown)
- Accents: #D47E30 (orange)
- Buttony: Zaoblené (border-radius 8px), bez stínů, subtle hover
- Input: Lehký border #D9BBB0
- Typografie: Sans-serif (inter), čistý design

#### **Návrh B: Moderní (Warm Earthy)**
- Background: #F7E6CA (cream)
- Kategorie s barvami:
  - Udělat: #D47E30 (orange)
  - Vymyslet: #4B6E48 (green)
  - Naplánovat: #AD9C8E (taupe)
  - Koupit: #6F4E37 (brown)
- Buttony: Skleněný efekt s warm stínem
- Input fields: Subtilní shadow s warm border
- Typografie: Bold headings, rounded

#### **Návrh C: Dark Mode (Zemitý dark)**
- Background: #331C08 (very dark brown) → #6F4E37 (rich brown)
- Text: #F5F5DC (ivory)
- Accents: #D47E30 (warm orange), #FFD3AC (peach)
- Kategorie (pastelové na dark):
  - Udělat: #FFD3AC (peach)
  - Vymyslet: #B2AC88 (olive/green)
  - Naplánovat: #D9BBB0 (mauve)
  - Koupit: #E8D59E (sand)
- Buttony: Solid warm barvy s warm glow efektem
- Input fields: Tmavé (#6F4E37) s peach border
- Ikony: Warm outlines
- Use case: Dark mode s teormu přírodních barev

---

### 5. Technická spec
- **Stack**: Next.js 16, Prisma, SQLite (jako hlucook)
- **Frontend**: React 19, Tailwind CSS
- **Backend**: Next.js API routes
- **Database schema**:
  ```prisma
  Task {
    id (PK)
    title (required)
    description (optional)
    duration (enum: 5min|15min|60min|90min+) (required)
    category (FK to Category) (required)
    deadline (datetime, optional)
    reminderDateTime (datetime, optional) – kdy poslat notifikaci
    url (optional)
    imageUrl (optional)
    repeatType (enum: none|weekly|monthly|daily, default: none)
    isArchived (boolean, default: false)
    createdAt
    updatedAt
  }
  
  Category {
    id (PK)
    name (required, unique)
    color (hex, optional) – barva dle palety
    createdAt
  }
  ```
- **Service Worker**: Push notifications 1 den před deadlinem
- **Responsive**: Mobile-first (głównie mobilní web)

---

### 6. MVP features
- ✅ CRUD pro tasky
- ✅ 4 views + přepínání
- ✅ Opakující se úkoly (měsíční repeat)
- ✅ Notifikace (push)
- ⏳ Offline mode (later)
- ⏳ Sync s cloudem (later)
- ⏳ Sdílení úkolů (later)

---

## Příští krok
1. Výběr jednoho ze 3 UI návrhů (A/B/C)
2. Setup projektu + database schema
3. Implementace braindump view + CRUD
4. Zbylé 3 views
5. Service Worker + notifikace
