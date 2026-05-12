# Nudge Project - Activity Log

## Popis projektu
Mobilní aplikace (web) pro osobní notifikace, bez závislosti na placených službách (mimo Claude).

---

## Plánované kroky

| Číslo | Úkol | Náročnost | Status | Poznamka |
|-------|------|-----------|--------|----------|
| 1 | Inicializace projektu (Next.js + Prisma + SQLite) | Nízká | Done | Next.js 16, Prisma 7 + better-sqlite3, seed s kategoriemi |
| 2 | Database schema (Task model s properties) | Nízká | Done | Task + Category modely, migrace aplikována |
| 3 | Vytvořit 3 UI návrhy (minimal/colorful/dark) | Střední | Done | Tailwind custom palette, Návrh B (Warm Earthy) vybrán |
| 4 | Výběr finálního UI návrhů | Nízká | Done | Návrh B – Warm Earthy (kategorie barevné, cream background) |
| 5 | Braindump view + CRUD formulář | Střední | Planned | Prioritá – rychlý input úkolů |
| 6 | Timeline view (řazení podle deadlinu) | Střední | Planned | Dnes/Tento týden/Později |
| 7 | Priority by duration view (skupiny 5/15/60/90+ min) | Nízká | Planned | Zobrazení podle času |
| 8 | Category view (skupiny dle kategorie) | Nízká | Planned | Statické + custom kategorie |
| 9 | Archiv view (archivované tasky + obnovení) | Nízká | Planned | Search/filter v archivu |
| 10 | Editace úkolů (modal/slide-in form) | Nízká | Planned | Všechna pole editovatelná |
| 11 | Custom kategorie (přidání nové z formuláře) | Nízká | Planned | On-the-fly vytváření kategorií |
| 12 | Opakující se úkoly (měsíční/týdenní/denní repeat) | Střední | Planned | Auto-vytvoření nového úkolu |
| 13 | Push notifikace (dle Reminder pole) | Střední | Planned | Vlastní čas notifikace per task |
| 14 | Validation – povinná pole (název, čas, kategorie) | Nízká | Planned | Frontend validace |
| 15 | Dark mode UI (Návrh C s teplými barvami) | Střední | Planned | Implementace dark design |
| 16 | Testing na mobilním zařízení | Nízká | Planned | Reálné testování notifikací + UI |

---

---

## 📋 Navržený postup (Development Roadmap)

### **Fáze 1: Setup & Foundation**
1. **Inicializace projektu** (Nízká náročnost)
   - `npx create-next-app@16 nudge --typescript --tailwind`
   - Prisma setup: `npm install @prisma/client`
   - SQLite databáze (file-based, ideální pro MVP)
   - Git init + základní struktura

2. **Database schema** (Nízká náročnost)
   - Prisma schema: Task + Category modely
   - Migration: `npx prisma migrate dev --name init`
   - Seed skript s default kategoriemi (Udělat, Vymyslet, Naplánovat, Koupit)

3. **UI návrh + styling** (Střední náročnost)
   - Rozhodnut: **Návrh B (Warm Earthy)** – nejflexibilnější pro kategorie + vizuálně čitný
   - Tailwind config: custom barvy z palety
   - Responsive layout (mobile-first)
   - Komponenty: Button, Input, Select, Card, Modal

---

### **Fáze 2: MVP Core Features**

4. **Braindump view + CRUD** (Střední náročnost) ⭐ PRIORITA
   - Formulář nahoře: Název + Duration + Kategorie + Povinná validace
   - Seznam aktivních úkolů pod formulářem
   - CRUD operace: Vytvoření, Editace (modal), Smazání
   - Checkbox pro archivaci → task se přesune do archivu

5. **Zbylé 4 views** (Nízká/Střední náročnost)
   - Timeline view: Dnes | Tento týden | Příští týden | Později
   - Duration view: Seskupení 5min | 15min | 60min | 90min+
   - Category view: Seskupení dle kategorií
   - Archive view: Archivované tasky + unarchive tlačítko

6. **Custom kategorie** (Nízká náročnost)
   - Input s dropdownem
   - Možnost přidat novou kategorii přímo z formuláře
   - Barvy pro kategorie (opakující se barvy z palety)

7. **Opakující se úkoly** (Střední náročnost)
   - Při checknutí tasku s repeatType ≠ none:
     - Vytvoř nový task s deadline = +1 měsíc/týden/den
     - Starý task se archivuje
   - Auto-scheduling mechanika

---

### **Fáze 3: Notifikace & Polish**

8. **Push notifikace** (Střední náročnost)
   - Service Worker: sluchaj `reminderDateTime`
   - Notifikace v zadaném čase (nezávislá na deadline)
   - Ověř funkci na reálném zařízení

9. **Validation & Error handling** (Nízká náročnost)
   - Frontend: Povinná pole (název, čas, kategorie)
   - Error messages
   - Toast notifikace (úspěch/chyba)

10. **UI Polish & Dark Mode** (Střední náročnost)
    - Dark mode toggle
    - Transitions a hover efekty
    - Responsive test na různých screen sizes

---

### **Fáze 4: Testing & Deployment**

11. **Functional testing** (Nízká náročnost)
    - CRUD všech úkolů ✓
    - Opakující se úkoly ✓
    - Notifikace ✓
    - Všechny views ✓

12. **Mobile testing** (Nízká náročnost)
    - Fyzické zařízení (iOS/Android)
    - Push notifikace real-time
    - Performance

---

## Poznámky
- Aktualizuji jen na tvůj výslovný pokyn
- Status: `Planned` → `In Progress` → `Done`
- **Vybraný UI návrh:** Návrh B (Warm Earthy) – barvy per kategorie
- **Deployment:** Vercel (pro Next.js) + SQLite na serveru (nebo lokalně s sync později)
